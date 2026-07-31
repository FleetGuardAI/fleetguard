import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/storage/secure_storage.dart';

class SelfieVerificationScreen extends StatefulWidget {
  const SelfieVerificationScreen({super.key});

  @override
  State<SelfieVerificationScreen> createState() => _SelfieVerificationScreenState();
}

class _SelfieVerificationScreenState extends State<SelfieVerificationScreen> {
  bool _isVerifying = false;

  void _captureAndVerify() async {
    setState(() => _isVerifying = true);
    await Future.delayed(const Duration(seconds: 2)); // Simulate AI face match

    await SecureStorage.setVerificationStatus('PENDING_APPROVAL');

    setState(() => _isVerifying = false);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('AI Face Verification Match: 95.8% Confidence')),
      );
      context.go('/auth/pending-approval');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI Face Verification')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            const SizedBox(height: 20),
            Text(
              'Selfie Verification',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Take a clear selfie to match against your Driving License photo using FleetGuard AI.',
              textAlign: TextAlign.center,
            ),
            const Spacer(),
            Center(
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Container(
                    width: 220,
                    height: 280,
                    decoration: BoxDecoration(
                      shape: BoxShape.rectangle,
                      borderRadius: BorderRadius.circular(110),
                      border: Border.all(
                        color: Theme.of(context).colorScheme.primary,
                        width: 4,
                      ),
                    ),
                    child: const Icon(Icons.face, size: 140, color: Colors.grey),
                  ),
                  if (_isVerifying) const CircularProgressIndicator(),
                ],
              ),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isVerifying ? null : _captureAndVerify,
                icon: const Icon(Icons.camera_alt),
                label: Text(_isVerifying ? 'Verifying with AI...' : 'Take Selfie & Verify'),
              ),
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
