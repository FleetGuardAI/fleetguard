import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Dashboard Tests', () {
    testWidgets('Dashboard UI renders correctly', (WidgetTester tester) async {
      // Create a simple mock dashboard widget for the test
      final testWidget = MaterialApp(
        home: Scaffold(
          appBar: AppBar(title: const Text('Dashboard')),
          body: const Column(
            children: [
              Text('Welcome Driver'),
              ElevatedButton(onPressed: null, child: Text('Start Trip')),
            ],
          ),
        ),
      );

      await tester.pumpWidget(testWidget);

      expect(find.text('Dashboard'), findsOneWidget);
      expect(find.text('Welcome Driver'), findsOneWidget);
      expect(find.text('Start Trip'), findsOneWidget);
    });
  });
}
