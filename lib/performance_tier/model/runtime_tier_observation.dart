import 'package:flutter/foundation.dart';

enum RuntimeTierStatus {
  inactive,
  pending,
  active,
  cooldown,
  recoveryPending,
  recovered;

  String get wireName {
    return switch (this) {
      RuntimeTierStatus.inactive => 'inactive',
      RuntimeTierStatus.pending => 'pending',
      RuntimeTierStatus.active => 'active',
      RuntimeTierStatus.cooldown => 'cooldown',
      RuntimeTierStatus.recoveryPending => 'recovery-pending',
      RuntimeTierStatus.recovered => 'recovered',
    };
  }
}

@immutable
class RuntimeTierObservation {
  const RuntimeTierObservation({
    this.status = RuntimeTierStatus.inactive,
    this.triggerReason,
    this.statusDuration = Duration.zero,
    this.downgradeTriggerCount = 0,
    this.recoveryTriggerCount = 0,
  });

  final RuntimeTierStatus status;
  final String? triggerReason;
  final Duration statusDuration;
  final int downgradeTriggerCount;
  final int recoveryTriggerCount;

  Map<String, Object?> toMap() {
    return <String, Object?>{
      'status': status.wireName,
      'triggerReason': triggerReason,
      'statusDurationMs': statusDuration.inMilliseconds,
      'downgradeTriggerCount': downgradeTriggerCount,
      'recoveryTriggerCount': recoveryTriggerCount,
    };
  }
}
