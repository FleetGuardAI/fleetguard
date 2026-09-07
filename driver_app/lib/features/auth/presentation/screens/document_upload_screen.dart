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
  Map<String, Map<String, dynamic>> _documents = {};
  bool _isLoading = true;
  
  final List<Map<String, String>> _requiredDocs = [
    {'type': 'license_front', 'title': 'Driving License (Front)'},
    {'type': 'license_back', 'title': 'Driving License (Back)'},
    {'type': 'aadhaar_front', 'title': 'Aadhaar Card (Front)'},
    {'type': 'aadhaar_back', 'title': 'Aadhaar Card (Back)'},
  ];

  @override
  void initState() {
    super.initState();
    _loadDocuments();
  }

  Future<void> _loadDocuments() async {
    try {
      final repo = ref.read(authRepositoryProvider);
      final docs = await repo.getDocuments();
      final newDocs = <String, Map<String, dynamic>>{};
      for (var d in docs) {
        if (d['category'] != null) {
          newDocs[d['category']] = d as Map<String, dynamic>;
        }
      }
      setState(() {
        _documents = newDocs;
        _isLoading = false;
      });
    } catch (e) {
      debugPrint("Error loading documents: $e");
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load documents')),
        );
      }
    }
  }

  bool get _allUploaded {
    for (var doc in _requiredDocs) {
      final status = _documents[doc['type']!]?['verification_status'];
      if (status == null || status == 'REJECTED') {
        return false;
      }
    }
    return true;
  }

  Widget _buildDocCard(String type, String title) {
    final docInfo = _documents[type];
    final status = docInfo?['verification_status'];
    final rejectionReason = docInfo?['rejection_reason'];
    final localState = docInfo?['local_state']; // For UPLOADING state

    IconData icon;
    Color iconColor;
    String subtitle;
    Widget? trailing;

    if (localState == 'UPLOADING') {
      icon = Icons.cloud_upload;
      iconColor = Colors.blue;
      subtitle = 'Uploading...';
      trailing = const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2));
    } else if (status == 'APPROVED') {
      icon = Icons.check_circle;
      iconColor = Colors.green;
      subtitle = 'Verified';
      trailing = const Icon(Icons.check, color: Colors.green);
    } else if (status == 'PENDING') {
      icon = Icons.access_time_filled;
      iconColor = Colors.orange;
      subtitle = 'Pending Verification';
      trailing = const Icon(Icons.hourglass_empty, color: Colors.orange);
    } else if (status == 'REJECTED') {
      icon = Icons.error;
      iconColor = Colors.red;
      subtitle = 'Rejected: ${rejectionReason ?? "Invalid document"}';
      trailing = const Icon(Icons.refresh, color: Colors.red);
    } else {
      icon = Icons.upload_file;
      iconColor = Theme.of(context).colorScheme.primary;
      subtitle = 'Tap to upload photo';
      trailing = const Icon(Icons.arrow_forward_ios, size: 16);
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        side: BorderSide(
          color: status == 'REJECTED' ? Colors.red.shade200 : Colors.transparent,
          width: 1,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: ListTile(
        leading: Icon(icon, color: iconColor, size: 32),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(
          subtitle, 
          style: TextStyle(
            color: status == 'REJECTED' ? Colors.red : null,
            fontWeight: status == 'REJECTED' ? FontWeight.w500 : null,
          )
        ),
        trailing: trailing,
        onTap: (localState == 'UPLOADING' || status == 'APPROVED' || status == 'PENDING') 
            ? null 
            : () => _captureAndUpload(type),
      ),
    );
  }

  void _captureAndUpload(String type) async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.camera, imageQuality: 70);
    
    if (pickedFile == null) return;

    setState(() {
      _documents[type] = {'local_state': 'UPLOADING'};
    });

    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.uploadDocument(File(pickedFile.path), type);
      await _loadDocuments(); // Refresh to get the PENDING status from backend
        
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Uploaded successfully!')),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _documents.remove(type);
        });
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
      body: _isLoading 
        ? const Center(child: CircularProgressIndicator())
        : Padding(
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
              child: ListView.builder(
                itemCount: _requiredDocs.length,
                itemBuilder: (context, index) {
                  final doc = _requiredDocs[index];
                  return _buildDocCard(doc['type']!, doc['title']!);
                },
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
