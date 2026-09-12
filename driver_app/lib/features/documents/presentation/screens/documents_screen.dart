import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../../../auth/data/auth_repository.dart';
import '../providers/documents_provider.dart';

class DocumentsScreen extends ConsumerStatefulWidget {
  const DocumentsScreen({super.key});

  @override
  ConsumerState<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends ConsumerState<DocumentsScreen> {
  final List<Map<String, String>> _requiredDocs = [
    {'type': 'license_front', 'title': 'Driving License (Front)'},
    {'type': 'license_back', 'title': 'Driving License (Back)'},
    {'type': 'aadhaar_front', 'title': 'Aadhaar Card (Front)'},
    {'type': 'aadhaar_back', 'title': 'Aadhaar Card (Back)'},
    {'type': 'selfie', 'title': 'Selfie'},
  ];

  Map<String, String> _uploadingStatus = {};

  Future<void> _uploadDoc(String type) async {
    final picker = ImagePicker();
    final file = await picker.pickImage(source: ImageSource.gallery);
    if (file == null) return;

    setState(() {
      _uploadingStatus[type] = 'UPLOADING';
    });

    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.uploadDocument(File(file.path), type);
      if (mounted) {
        ref.invalidate(documentsProvider);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to upload $type: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _uploadingStatus.remove(type);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final docsAsync = ref.watch(documentsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('My Documents')),
      body: docsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text('Error loading documents: $err', textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.invalidate(documentsProvider),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (docs) {
          final docMap = <String, Map<String, dynamic>>{};
          for (var d in docs) {
            if (d['category'] != null) {
              docMap[d['category']] = d as Map<String, dynamic>;
            }
          }

          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(documentsProvider);
            },
            child: ListView.builder(
              padding: const EdgeInsets.all(16.0),
              itemCount: _requiredDocs.length,
              itemBuilder: (context, index) {
                final docDef = _requiredDocs[index];
                final type = docDef['type']!;
                final title = docDef['title']!;
                
                final docInfo = docMap[type];
                final status = docInfo?['verification_status'];
                final rejectionReason = docInfo?['rejection_reason'];
                
                final isUploading = _uploadingStatus[type] == 'UPLOADING';

                IconData icon;
                Color iconColor;
                String subtitle;
                Widget? trailing;

                if (isUploading) {
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
                  trailing = ElevatedButton(
                    onPressed: () => _uploadDoc(type),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
                    child: const Text('Re-upload'),
                  );
                } else {
                  icon = Icons.file_upload;
                  iconColor = Colors.grey;
                  subtitle = 'Not Uploaded';
                  trailing = ElevatedButton(
                    onPressed: () => _uploadDoc(type),
                    child: const Text('Upload'),
                  );
                }

                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    leading: Icon(icon, size: 36, color: iconColor),
                    title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text(subtitle, style: TextStyle(color: status == 'REJECTED' ? Colors.red : null)),
                    trailing: trailing,
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
