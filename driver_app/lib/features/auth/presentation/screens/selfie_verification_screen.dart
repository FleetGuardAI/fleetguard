import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../../../core/storage/secure_storage.dart';
import '../../data/auth_repository.dart';

class SelfieVerificationScreen extends ConsumerStatefulWidget {
  const SelfieVerificationScreen({super.key});

  @override
  ConsumerState<SelfieVerificationScreen> createState() => _SelfieVerificationScreenState();
}

class _SelfieVerificationScreenState extends ConsumerState<SelfieVerificationScreen> {
  bool _isVerifying = false;

  File? _selfieFile;

  void _captureAndVerify() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(
      source: ImageSource.camera, 
      preferredCameraDevice: CameraDevice.front,
      imageQuality: 70
    );
    
    if (pickedFile == null) return;
    
    setState(() {
      _selfieFile = File(pickedFile.path);
      _isVerifying = true;
    });
    
    try {
      final repo = ref.read(authRepositoryProvider);

      // 1. Upload Selfie
      await repo.uploadDocument(_selfieFile!, 'selfie');

      // 2. Trigger Face Verify
      final verifyResponse = await repo.verifyFace();

      await SecureStorage.setVerificationStatus('PENDING_APPROVAL');

      setState(() => _isVerifying = false);

      if (mounted) {
        final confidence = (verifyResponse['confidence'] * 100).toStringAsFixed(1);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('AI Face Verification Match: $confidence% Confidence')),
        );
        context.go('/auth/welcome');
      }
    } catch (e) {
      setState(() => _isVerifying = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Face Verification failed: $e')),
        );
      }
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
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(110),
                      child: _selfieFile != null 
                          ? Image.file(_selfieFile!, fit: BoxFit.cover)
                          : const Icon(Icons.face, size: 140, color: Colors.grey),
                    ),
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
