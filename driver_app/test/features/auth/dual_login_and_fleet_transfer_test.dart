import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:fleetguard_driver/features/auth/data/auth_repository.dart';
import 'package:fleetguard_driver/features/auth/presentation/screens/driver_login_screen.dart';
import 'package:fleetguard_driver/features/auth/presentation/screens/fleet_mismatch_screen.dart';

class FakeAuthRepository extends AuthRepository {
  FakeAuthRepository() : super(null as dynamic);

  bool transferRequested = false;
  int? requestedTargetCompanyId;
  String? requestedInviteToken;

  @override
  Future<Map<String, dynamic>> resolveQr(String qrData, [String? phoneNumber]) async {
    if (qrData.contains('mismatch')) {
      return {
        'valid': true,
        'action': 'CONFIRM_SWITCH',
        'is_same_fleet': false,
        'is_fleet_mismatch': true,
        'current_company_id': 101,
        'current_company_name': 'Fleet Alpha Logistics',
        'target_company_id': 202,
        'target_company_name': 'Fleet Beta Express',
        'invite_token': qrData,
      };
    } else if (qrData.contains('same_fleet')) {
      return {
        'valid': true,
        'action': 'LOGIN',
        'is_same_fleet': true,
        'is_fleet_mismatch': false,
        'company_id': 101,
        'company_name': 'Fleet Alpha Logistics',
        'invite_token': qrData,
      };
    }
    return {
      'valid': false,
      'action': 'INVALID',
      'message': 'Invalid QR credential',
    };
  }

  @override
  Future<Map<String, dynamic>> requestFleetTransfer(String inviteToken, int targetCompanyId) async {
    transferRequested = true;
    requestedTargetCompanyId = targetCompanyId;
    requestedInviteToken = inviteToken;
    return {
      'id': 789,
      'status': 'PENDING_APPROVAL',
      'message': 'Fleet transfer request submitted successfully.',
    };
  }
}

void main() {
  group('Dual Login & Fleet Switch UI Tests', () {
    testWidgets('DriverLoginScreen renders both QR and Mobile login options', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: DriverLoginScreen(),
          ),
        ),
      );

      // Verify title & branding
      expect(find.text('the vahan'), findsOneWidget);
      expect(find.text('DRIVER PARTNER'), findsOneWidget);

      // Verify Dual Login Options
      expect(find.text('Login with QR Code'), findsOneWidget);
      expect(find.text('Login with Mobile Number'), findsOneWidget);

      // Verify Icons
      expect(find.byIcon(Icons.qr_code_scanner_rounded), findsOneWidget);
      expect(find.byIcon(Icons.phone_android_rounded), findsOneWidget);
    });

    testWidgets('FleetMismatchScreen renders comparative fleets and required disclosure', (tester) async {
      final fakeRepo = FakeAuthRepository();

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            authRepositoryProvider.overrideWithValue(fakeRepo),
          ],
          child: const MaterialApp(
            home: FleetMismatchScreen(
              currentCompanyName: 'Fleet Alpha Logistics',
              targetCompanyName: 'Fleet Beta Express',
              targetCompanyId: 202,
              inviteToken: 'test_invite_token_b',
            ),
          ),
        ),
      );

      // Verify header
      expect(find.text('Switching Fleet Assignment'), findsOneWidget);

      // Verify Current Fleet and New Fleet
      expect(find.text('Fleet Alpha Logistics'), findsOneWidget);
      expect(find.text('Fleet Beta Express'), findsOneWidget);
      expect(find.text('CURRENT FLEET'), findsOneWidget);
      expect(find.text('NEW FLEET (SCANNED)'), findsOneWidget);

      // Verify Required Disclosure Text
      expect(
        find.text(
          'You are switching to a new fleet. Your current fleet assignment will be replaced only after the new registration and approval process is completed.',
        ),
        findsOneWidget,
      );

      // Verify Action Buttons
      expect(find.text('Continue Registration'), findsOneWidget);
      expect(find.text('Cancel & Stay in Current Fleet'), findsOneWidget);
    });

    test('FakeAuthRepository correctly resolves same fleet and mismatched fleet', () async {
      final repo = FakeAuthRepository();

      final sameFleetRes = await repo.resolveQr('invite_same_fleet');
      expect(sameFleetRes['valid'], true);
      expect(sameFleetRes['action'], 'LOGIN');
      expect(sameFleetRes['is_same_fleet'], true);

      final mismatchRes = await repo.resolveQr('invite_mismatch_beta');
      expect(mismatchRes['valid'], true);
      expect(mismatchRes['action'], 'CONFIRM_SWITCH');
      expect(mismatchRes['is_fleet_mismatch'], true);
      expect(mismatchRes['current_company_id'], 101);
      expect(mismatchRes['target_company_id'], 202);
    });
  });
}
