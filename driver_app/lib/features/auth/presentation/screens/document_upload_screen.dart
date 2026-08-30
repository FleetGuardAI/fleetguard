import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../data/auth_repository.dart';

class DocumentUploadScreen extends ConsumerStatefulWidget {
  const DocumentUploadScreen({super.key});

  @override
  ConsumerState<DocumentUploadScreen> createState() => _DocumentUploadScreenState();
}

class _DocumentUploadScreenState extends ConsumerState<DocumentUploadScreen> {
  bool _dlFrontUploaded = false;
  bool _dlBackUploaded = false;
  bool _aadhaarFrontUploaded = false;
  bool _aadhaarBackUploaded = false;

  bool get _allUploaded =>
      _dlFrontUploaded && _dlBackUploaded && _aadhaarFrontUploaded && _aadhaarBackUploaded;

  Widget _buildDocCard(String title, bool isUploaded, VoidCallback onTap) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: Icon(
          isUploaded ? Icons.check_circle : Icons.upload_file,
          color: isUploaded ? Colors.green : Theme.of(context).colorScheme.primary,
          size: 32,
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(isUploaded ? 'Uploaded & Verified' : 'Tap to upload photo'),
        trailing: isUploaded ? const Icon(Icons.edit, size: 20) : const Icon(Icons.arrow_forward_ios, size: 16),
        onTap: onTap,
      ),
    );
  }

  void _captureAndUpload(String type) async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.camera, imageQuality: 70);
    
    if (pickedFile == null) return;

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Uploading $type...')),
      );
    }

    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.uploadDocument(File(pickedFile.path), type);
        
      setState(() {
        if (type == 'license_front') _dlFrontUploaded = true;
        if (type == 'license_back') _dlBackUploaded = true;
        if (type == 'aadhaar_front') _aadhaarFrontUploaded = true;
        if (type == 'aadhaar_back') _aadhaarBackUploaded = true;
      });
        
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Uploaded successfully!')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Upload failed: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Upload Documents')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Identity Documents',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text('Upload clear photos of your Driving License and Aadhaar Card.'),
            const SizedBox(height: 24),
            Expanded(
              child: ListView(
                children: [
                  _buildDocCard('Driving License (Front)', _dlFrontUploaded, () => _captureAndUpload('license_front')),
                  _buildDocCard('Driving License (Back)', _dlBackUploaded, () => _captureAndUpload('license_back')),
                  _buildDocCard('Aadhaar Card (Front)', _aadhaarFrontUploaded, () => _captureAndUpload('aadhaar_front')),
                  _buildDocCard('Aadhaar Card (Back)', _aadhaarBackUploaded, () => _captureAndUpload('aadhaar_back')),
                ],
              ),
            ),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _allUploaded
                    ? () => context.go('/auth/selfie-verify')
                    : null,
                child: const Text('Next: Face Verification'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
