import 'package:flutter_performance_tier/performance_tier/performance_tier.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('RuntimeTierController', () {
    test('keeps base tier when no runtime pressure signal', () {
      final clock = _FakeClock(DateTime(2026, 2, 25, 12, 0, 0));
      final controller = RuntimeTierController(now: clock.now);

      final adjustment = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(
          collectedAt: clock.now(),
          thermalStateLevel: 0,
          isLowPowerModeEnabled: false,
        ),
      );

      expect(adjustment.tier, TierLevel.t3Ultra);
      expect(adjustment.reasons, isEmpty);
      expect(adjustment.observation.status, RuntimeTierStatus.inactive);
      expect(adjustment.observation.triggerReason, isNull);
      expect(adjustment.observation.statusDuration, Duration.zero);
      expect(adjustment.observation.downgradeTriggerCount, 0);
      expect(adjustment.observation.recoveryTriggerCount, 0);
    });

    test('waits for debounce window before applying downgrade', () {
      final clock = _FakeClock(DateTime(2026, 2, 25, 12, 0, 0));
      final controller = RuntimeTierController(
        now: clock.now,
        config: const RuntimeTierControllerConfig(
          downgradeDebounce: Duration(seconds: 5),
          recoveryCooldown: Duration(seconds: 15),
        ),
      );

      final first = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(
          collectedAt: clock.now(),
          isLowPowerModeEnabled: true,
        ),
      );
      expect(first.tier, TierLevel.t3Ultra);
      expect(first.reasons.single, contains('Runtime downgrade pending'));
      expect(first.observation.status, RuntimeTierStatus.pending);
      expect(first.observation.triggerReason, 'lowPowerMode=true');
      expect(first.observation.statusDuration, Duration.zero);
      expect(first.observation.downgradeTriggerCount, 0);
      expect(first.observation.recoveryTriggerCount, 0);

      clock.advance(const Duration(seconds: 5));
      final second = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(
          collectedAt: clock.now(),
          isLowPowerModeEnabled: true,
        ),
      );
      expect(second.tier, TierLevel.t2High);
      expect(second.reasons.single, contains('Runtime downgrade active'));
      expect(second.observation.status, RuntimeTierStatus.active);
      expect(second.observation.triggerReason, 'lowPowerMode=true');
      expect(second.observation.statusDuration, Duration.zero);
      expect(second.observation.downgradeTriggerCount, 1);
      expect(second.observation.recoveryTriggerCount, 0);

      clock.advance(const Duration(seconds: 2));
      final third = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(
          collectedAt: clock.now(),
          isLowPowerModeEnabled: true,
        ),
      );
      expect(third.observation.status, RuntimeTierStatus.active);
      expect(third.observation.statusDuration, const Duration(seconds: 2));
      expect(third.observation.downgradeTriggerCount, 1);
    });

    test('recovers in throttled upgrade steps after cooldown', () {
      final clock = _FakeClock(DateTime(2026, 2, 25, 12, 0, 0));
      final controller = RuntimeTierController(
        now: clock.now,
        config: const RuntimeTierControllerConfig(
          downgradeDebounce: Duration.zero,
          recoveryCooldown: Duration(seconds: 20),
          upgradeDebounce: Duration(seconds: 5),
        ),
      );

      final activated = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(collectedAt: clock.now(), thermalStateLevel: 2),
      );
      expect(activated.tier, TierLevel.t1Mid);
      expect(activated.observation.status, RuntimeTierStatus.active);
      expect(
        activated.observation.triggerReason,
        contains('thermalState=serious(level=2)'),
      );
      expect(activated.observation.downgradeTriggerCount, 1);
      expect(activated.observation.recoveryTriggerCount, 0);

      clock.advance(const Duration(seconds: 10));
      final inCooldown = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(collectedAt: clock.now(), thermalStateLevel: 0),
      );
      expect(inCooldown.tier, TierLevel.t1Mid);
      expect(inCooldown.reasons.single, contains('Runtime cooldown active'));
      expect(inCooldown.observation.status, RuntimeTierStatus.cooldown);
      expect(
        inCooldown.observation.triggerReason,
        contains('thermalState=serious(level=2)'),
      );
      expect(inCooldown.observation.statusDuration, Duration.zero);
      expect(inCooldown.observation.downgradeTriggerCount, 1);
      expect(inCooldown.observation.recoveryTriggerCount, 0);

      clock.advance(const Duration(seconds: 3));
      final stillInCooldown = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(collectedAt: clock.now(), thermalStateLevel: 0),
      );
      expect(stillInCooldown.observation.status, RuntimeTierStatus.cooldown);
      expect(
        stillInCooldown.observation.statusDuration,
        const Duration(seconds: 3),
      );
      expect(stillInCooldown.observation.downgradeTriggerCount, 1);
      expect(stillInCooldown.observation.recoveryTriggerCount, 0);

      clock.advance(const Duration(seconds: 8));
      final firstUpgrade = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(collectedAt: clock.now(), thermalStateLevel: 0),
      );
      expect(firstUpgrade.tier, TierLevel.t2High);
      expect(firstUpgrade.reasons.single, contains('Runtime upgrade step'));
      expect(firstUpgrade.observation.status, RuntimeTierStatus.active);

      clock.advance(const Duration(seconds: 4));
      final pendingUpgrade = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(collectedAt: clock.now(), thermalStateLevel: 0),
      );
      expect(pendingUpgrade.tier, TierLevel.t2High);
      expect(
        pendingUpgrade.reasons.single,
        contains('Runtime recovery pending'),
      );
      expect(
        pendingUpgrade.observation.status,
        RuntimeTierStatus.recoveryPending,
      );

      clock.advance(const Duration(seconds: 1));
      final recovered = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(collectedAt: clock.now(), thermalStateLevel: 0),
      );
      expect(recovered.tier, TierLevel.t3Ultra);
      expect(recovered.reasons.single, contains('Runtime downgrade recovered'));
      expect(recovered.observation.status, RuntimeTierStatus.recovered);
      expect(recovered.observation.downgradeTriggerCount, 1);
      expect(recovered.observation.recoveryTriggerCount, 1);
    });

    test('increments downgrade trigger count when pressure escalates', () {
      final clock = _FakeClock(DateTime(2026, 2, 25, 12, 0, 0));
      final controller = RuntimeTierController(
        now: clock.now,
        config: const RuntimeTierControllerConfig(
          downgradeDebounce: Duration.zero,
          recoveryCooldown: Duration.zero,
        ),
      );

      final first = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(
          collectedAt: clock.now(),
          isLowPowerModeEnabled: true,
        ),
      );
      expect(first.observation.status, RuntimeTierStatus.active);
      expect(first.observation.downgradeTriggerCount, 1);

      clock.advance(const Duration(seconds: 1));
      final escalated = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(
          collectedAt: clock.now(),
          thermalStateLevel: 2,
          isLowPowerModeEnabled: true,
        ),
      );
      expect(escalated.observation.status, RuntimeTierStatus.active);
      expect(escalated.observation.downgradeTriggerCount, 2);

      clock.advance(const Duration(seconds: 1));
      final sameLevel = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(
          collectedAt: clock.now(),
          thermalStateLevel: 2,
          isLowPowerModeEnabled: true,
        ),
      );
      expect(sameLevel.observation.status, RuntimeTierStatus.active);
      expect(sameLevel.observation.downgradeTriggerCount, 2);
    });

    test('maps critical thermal pressure to the lowest tier', () {
      final clock = _FakeClock(DateTime(2026, 2, 25, 12, 0, 0));
      final controller = RuntimeTierController(
        now: clock.now,
        config: const RuntimeTierControllerConfig(
          downgradeDebounce: Duration.zero,
          recoveryCooldown: Duration.zero,
        ),
      );

      final adjustment = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(
          collectedAt: clock.now(),
          thermalState: 'critical',
          thermalStateLevel: null,
        ),
      );

      expect(adjustment.tier, TierLevel.t0Low);
      expect(adjustment.reasons.single, contains('thermalState=critical'));
      expect(adjustment.observation.status, RuntimeTierStatus.active);
      expect(
        adjustment.observation.triggerReason,
        contains('thermalState=critical'),
      );
    });

    test('downgrades tier when memory pressure is critical', () {
      final clock = _FakeClock(DateTime(2026, 2, 25, 12, 0, 0));
      final controller = RuntimeTierController(
        now: clock.now,
        config: const RuntimeTierControllerConfig(
          downgradeDebounce: Duration.zero,
          recoveryCooldown: Duration.zero,
        ),
      );

      final adjustment = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(
          collectedAt: clock.now(),
          thermalStateLevel: 0,
          isLowPowerModeEnabled: false,
          memoryPressureState: 'critical',
        ),
      );

      expect(adjustment.tier, TierLevel.t1Mid);
      expect(adjustment.reasons.single, contains('memoryPressure=critical'));
      expect(adjustment.observation.status, RuntimeTierStatus.active);
      expect(
        adjustment.observation.triggerReason,
        contains('memoryPressure=critical'),
      );
    });

    test('ignores frame-drop signal when the feature switch is disabled', () {
      final clock = _FakeClock(DateTime(2026, 2, 25, 12, 0, 0));
      final controller = RuntimeTierController(
        now: clock.now,
        config: const RuntimeTierControllerConfig(
          downgradeDebounce: Duration.zero,
          recoveryCooldown: Duration.zero,
          enableFrameDropSignal: false,
        ),
      );

      final adjustment = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(
          collectedAt: clock.now(),
          thermalStateLevel: 0,
          frameDropState: 'critical',
          frameDropLevel: 2,
          frameDropRate: 0.4,
        ),
      );

      expect(adjustment.tier, TierLevel.t3Ultra);
      expect(adjustment.reasons, isEmpty);
      expect(adjustment.observation.status, RuntimeTierStatus.inactive);
    });

    test('downgrades tier when frame-drop signal is critical', () {
      final clock = _FakeClock(DateTime(2026, 2, 25, 12, 0, 0));
      final controller = RuntimeTierController(
        now: clock.now,
        config: const RuntimeTierControllerConfig(
          downgradeDebounce: Duration.zero,
          recoveryCooldown: Duration.zero,
          enableFrameDropSignal: true,
        ),
      );

      final adjustment = controller.adjust(
        baseTier: TierLevel.t3Ultra,
        signals: _iosSignals(
          collectedAt: clock.now(),
          thermalStateLevel: 0,
          frameDropState: 'critical',
          frameDropLevel: 2,
          frameDropRate: 0.35,
        ),
      );

      expect(adjustment.tier, TierLevel.t1Mid);
      expect(adjustment.reasons.single, contains('frameDrop=critical'));
      expect(adjustment.reasons.single, contains('rate=35.0%'));
      expect(adjustment.observation.status, RuntimeTierStatus.active);
      expect(
        adjustment.observation.triggerReason,
        contains('frameDrop=critical'),
      );
    });
  });
}

DeviceSignals _iosSignals({
  required DateTime collectedAt,
  int? thermalStateLevel,
  String? thermalState,
  bool? isLowPowerModeEnabled,
  String? memoryPressureState,
  int? memoryPressureLevel,
  String? frameDropState,
  int? frameDropLevel,
  double? frameDropRate,
  int? frameDroppedCount,
  int? frameSampledCount,
}) {
  return DeviceSignals(
    platform: 'ios',
    collectedAt: collectedAt,
    thermalStateLevel: thermalStateLevel,
    thermalState: thermalState,
    isLowPowerModeEnabled: isLowPowerModeEnabled,
    memoryPressureState: memoryPressureState,
    memoryPressureLevel: memoryPressureLevel,
    frameDropState: frameDropState,
    frameDropLevel: frameDropLevel,
    frameDropRate: frameDropRate,
    frameDroppedCount: frameDroppedCount,
    frameSampledCount: frameSampledCount,
  );
}

class _FakeClock {
  _FakeClock(this._value);

  DateTime _value;

  DateTime now() => _value;

  void advance(Duration delta) {
    _value = _value.add(delta);
  }
}
