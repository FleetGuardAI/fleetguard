import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/material.dart';
import 'package:fleetguard_owner/main.dart';
import 'package:fleetguard_owner/core/providers/mock_data_provider.dart';

// 1x1 transparent PNG for offline testing
final Uint8List _transparentImage = Uint8List.fromList([
  137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82, 
  0, 0, 0, 1, 0, 0, 0, 1, 8, 6, 0, 0, 0, 31, 21, 196, 137, 
  0, 0, 0, 11, 73, 68, 65, 84, 8, 215, 99, 96, 0, 2, 0, 0, 
  5, 0, 1, 226, 38, 5, 155, 0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130
]);

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    final transparentMemoryImage = MemoryImage(_transparentImage);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          mockAvatarProvider.overrideWithValue(transparentMemoryImage),
          mockMapProvider.overrideWithValue(transparentMemoryImage),
        ],
        child: const FleetGuardOwnerApp(),
      ),
    );

    // Verify that the app builds and shows the Dashboard (which has 'FleetGuard' text).
    expect(find.text('FleetGuard'), findsOneWidget);
  });
}
