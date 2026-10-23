import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/config/theme/app_colors.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../data/auth_repository.dart';

class QrScanScreen extends ConsumerStatefulWidget {
  const QrScanScreen({super.key});

  @override
  ConsumerState<QrScanScreen> createState() => _QrScanScreenState();
}

class _QrScanScreenState extends ConsumerState<QrScanScreen> {
  bool _isProcessing = false;
  final MobileScannerController _controller = MobileScannerController();

  void _onDetect(BarcodeCapture capture) {
    if (_isProcessing) return;
    final List<Barcode> barcodes = capture.barcodes;
    for (final barcode in barcodes) {
      if (barcode.rawValue != null) {
        final code = barcode.rawValue!;
        _processInviteCode(code);
        break;
      }
    }
  }

  Future<void> _processInviteCode(String rawCode) async {
    setState(() => _isProcessing = true);

    try {
      final repo = ref.read(authRepositoryProvider);
      final phone = await SecureStorage.getPhoneNumber();
      final response = await repo.resolveQr(rawCode, phone);

      if (!mounted) return;

      if (response['valid'] != true) {
        setState(() => _isProcessing = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(response['message'] ?? 'Invalid, expired, or revoked fleet QR code.'),
            backgroundColor: AppColors.error,
          ),
        );
        return;
      }

      final action = response['action']?.toString() ?? 'VERIFY_PHONE';
      final companyName = response['company_name']?.toString() ?? 'Fleet Partner';
      final companyId = response['company_id'];
      final inviteToken = response['invite_token']?.toString() ?? rawCode;

      if (companyName.isNotEmpty) {
        await SecureStorage.setCompanyName(companyName);
      }
      if (inviteToken.isNotEmpty) {
        await SecureStorage.setInviteToken(inviteToken);
      }
      if (companyId != null && companyId is int) {
        await SecureStorage.setCompanyId(companyId);
      }

      if (action == 'LOGIN') {
        // Case A: Driver is already registered, approved, and belongs to this fleet
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Welcome back to $companyName!'),
            backgroundColor: AppColors.success,
          ),
        );
        context.go('/dashboard');
      } else if (action == 'CONFIRM_SWITCH') {
        // Case B: Driver belongs to Fleet A but scanned Fleet B
        context.push(
          '/auth/fleet-mismatch',
          extra: {
            'current_company_name': response['current_company_name'] ?? 'Current Fleet',
            'target_company_name': response['target_company_name'] ?? companyName,
            'target_company_id': response['target_company_id'] ?? companyId,
            'invite_token': inviteToken,
          },
        );
      } else if (action == 'TRANSFER_PENDING') {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('A fleet transfer is already pending approval by the fleet manager.'),
            backgroundColor: AppColors.warning,
          ),
        );
        context.go('/auth/pending-approval');
      } else if (action == 'PENDING_DOCUMENTS') {
        context.go('/auth/profile');
      } else if (action == 'PENDING_APPROVAL') {
        context.go('/auth/pending-approval');
      } else {
        // VERIFY_PHONE: Driver identity verification needed before account access
        context.go(
          '/auth/phone-verify',
          extra: {
            'company_name': companyName,
            'invite_token': inviteToken,
          },
        );
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _isProcessing = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error validating QR code: $e'),
          backgroundColor: AppColors.error,
        ),
      );
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan Fleet QR'),
        centerTitle: true,
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: _controller,
            onDetect: _onDetect,
          ),
          // Scanner Overlay Frame
          Center(
            child: Container(
              width: 260,
              height: 260,
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.primaryLight, width: 4),
                borderRadius: BorderRadius.circular(20),
              ),
            ),
          ),
          // Instruction Card
          Positioned(
            bottom: 40,
            left: 24,
            right: 24,
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.92),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.08),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.qr_code_2_rounded, color: AppColors.primary, size: 28),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Text(
                          'Point your camera at the official The Vahan Fleet QR Code',
                          style: TextStyle(
                            color: AppColors.deepGraphite,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Loading indicator overlay during server validation
          if (_isProcessing)
            Container(
              color: Colors.black.withOpacity(0.55),
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 22),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      CircularProgressIndicator(color: AppColors.primary),
                      SizedBox(height: 16),
                      Text(
                        'Verifying Fleet QR...',
                        style: TextStyle(
                          color: AppColors.deepGraphite,
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
