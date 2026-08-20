import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../../core/router/app_router.dart';
import 'package:dio/dio.dart';

import 'package:mobile_scanner/mobile_scanner.dart';

class QRScanScreen extends ConsumerStatefulWidget {
  const QRScanScreen({super.key});

  @override
  ConsumerState<QRScanScreen> createState() => _QRScanScreenState();
}

class _QRScanScreenState extends ConsumerState<QRScanScreen> {
  final MobileScannerController _scannerController = MobileScannerController();
  bool _isLoading = false;
  String? _error;
  bool _hasScanned = false;

  @override
  void dispose() {
    _scannerController.dispose();
    super.dispose();
  }

  Future<void> _loginWithToken(String token) async {
    if (_hasScanned) return;
    
    setState(() {
      _hasScanned = true;
      _isLoading = true;
      _error = null;
    });

    try {
      final api = ref.read(apiClientProvider);
      final response = await api.dio.post(
        '/api/v1/auth/owner-qr/verify',
        data: {'pairing_token': token},
      );

      final accessToken = response.data['access_token'];
      if (accessToken != null) {
        await SecureStorage.setAccessToken(accessToken);
        ref.read(authStateProvider.notifier).state = true;
        if (mounted) {
          context.go('/dashboard');
        }
      }
    } on DioException catch (e) {
      setState(() {
        _error = e.response?.data?['detail'] ?? 'Login failed. Invalid or expired QR token.';
        _hasScanned = false;
      });
    } catch (e) {
      setState(() {
        _error = 'An unexpected error occurred.';
        _hasScanned = false;
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 48),
            Text(
              'Owner Login',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 24.0),
              child: Text(
                'Scan the QR code from the FleetGuard Dashboard to log in.',
                textAlign: TextAlign.center,
              ),
            ),
            const SizedBox(height: 48),
            
            Expanded(
              child: Stack(
                children: [
                  MobileScanner(
                    controller: _scannerController,
                    onDetect: (capture) {
                      if (_hasScanned) return;
                      final List<Barcode> barcodes = capture.barcodes;
                      for (final barcode in barcodes) {
                        if (barcode.rawValue != null) {
                          _loginWithToken(barcode.rawValue!);
                          break;
                        }
                      }
                    },
                  ),
                  if (_isLoading)
                    Container(
                      color: Colors.black54,
                      child: const Center(
                        child: CircularProgressIndicator(),
                      ),
                    ),
                ],
              ),
            ),
            
            if (_error != null)
              Padding(
                padding: const EdgeInsets.all(24.0),
                child: Text(
                  _error!,
                  style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
              ),
              
            const SizedBox(height: 48),
          ],
        ),
      ),
    );
  }
}
