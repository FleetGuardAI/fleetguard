import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fleetguard_owner/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: FleetGuardOwnerApp(),
      ),
    );

    // Initial route should be the auth screen or loading
    expect(find.byType(ProviderScope), findsOneWidget);
  });
}
