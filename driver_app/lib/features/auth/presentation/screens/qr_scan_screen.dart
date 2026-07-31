import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../../../../core/config/theme/app_colors.dart';

class QrScanScreen extends StatefulWidget {
  const QrScanScreen({super.key});

  @override
  State<QrScanScreen> createState() => _QrScanScreenState();
}

class _QrScanScreenState extends State<QrScanScreen> {
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

  void _processInviteCode(String rawCode) {
    setState(() => _isProcessing = true);
    
    // Parse invite token from QR code string (e.g., fleetguard://invite?token=xyz123)
    String token = rawCode;
    if (rawCode.contains("token=")) {
      final uri = Uri.parse(rawCode);
      token = uri.queryParameters['token'] ?? rawCode;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Fleet invite QR scanned successfully!')),
    );

    context.go(
      '/auth/phone-verify',
      extra: {
        'company_name': 'FleetGuard Partner Fleet',
        'invite_token': token,
      },
    );
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
        title: const Text('Join Fleet'),
        centerTitle: true,
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: _controller,
            onDetect: _onDetect,
          ),
          // Scanner Overlay
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
          Positioned(
            bottom: 40,
            left: 24,
            right: 24,
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.7),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Text(
                    'Scan the FleetGuard QR Code provided by your fleet manager to join',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.white, fontSize: 14),
                  ),
                ),
                const SizedBox(height: 16),
                OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.white,
                    side: const BorderSide(color: Colors.white),
                  ),
                  onPressed: () {
                    // Manual demo bypass button
                    _processInviteCode("demo_invite_token_2026");
                  },
                  icon: const Icon(Icons.qr_code),
                  label: const Text('Demo: Skip QR Scan'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
