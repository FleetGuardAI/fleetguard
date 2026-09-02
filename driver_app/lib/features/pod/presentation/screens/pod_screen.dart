import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:syncfusion_flutter_signaturepad/signaturepad.dart';
import 'package:path_provider/path_provider.dart';

import '../../data/pod_repository.dart';

class PodScreen extends ConsumerStatefulWidget {

  const PodScreen({super.key, required this.tripId});
  final int tripId;

  @override
  ConsumerState<PodScreen> createState() => _PodScreenState();
}

class _PodScreenState extends ConsumerState<PodScreen> {
  final _remarksController = TextEditingController();
  final _receiverController = TextEditingController();

  final GlobalKey<SfSignaturePadState> _signaturePadKey = GlobalKey();
  
  File? _signatureFile;
  File? _photoFile;
  
  bool _photoCaptured = false;
  bool _signatureCaptured = false;
  bool _isSubmitting = false;

  void _capturePhoto() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.camera, imageQuality: 70);
    if (picked != null) {
      setState(() {
        _photoFile = File(picked.path);
        _photoCaptured = true;
      });
    }
  }

  void _saveSignature() async {
    try {
      final data = await _signaturePadKey.currentState!.toImage(pixelRatio: 3.0);
      final byteData = await data.toByteData(format: ui.ImageByteFormat.png);
      final bytes = byteData!.buffer.asUint8List();

      final directory = await getApplicationDocumentsDirectory();
      final file = File('${directory.path}/signature_${widget.tripId}.png');
      await file.writeAsBytes(bytes);

      setState(() {
        _signatureFile = file;
        _signatureCaptured = true;
      });
    } catch (e) {
      debugPrint('Error saving signature: $e');
    }
  }

  void _clearSignature() {
    _signaturePadKey.currentState?.clear();
    setState(() {
      _signatureFile = null;
      _signatureCaptured = false;
    });
  }

  void _submitPod() async {
    if (!_signatureCaptured || _signatureFile == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please capture customer signature first')),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    
    try {
      final repo = ref.read(podRepositoryProvider);
      
      final String signatureUrl = await repo.uploadFile(_signatureFile!, 'signature');
      String? photoUrl;
      if (_photoFile != null) {
        photoUrl = await repo.uploadFile(_photoFile!, 'pod_photo');
      }

      await repo.submitPod(
        tripId: widget.tripId,
        receiverName: _receiverController.text.trim(),
        remarks: _remarksController.text.trim(),
        signatureUrl: signatureUrl,
        photoUrl: photoUrl,
      );

      setState(() => _isSubmitting = false);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Proof of Delivery (POD) submitted. Trip completed!')),
        );
        context.go('/dashboard');
      }
    } catch (e) {
      setState(() => _isSubmitting = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Proof of Delivery — Trip #${widget.tripId}')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Customer Delivery Receipt', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            TextFormField(
              controller: _receiverController,
              decoration: const InputDecoration(labelText: 'Receiver Name', prefixIcon: Icon(Icons.person)),
            ),
            const SizedBox(height: 16),
            // Digital Signature Pad Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    const Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Customer Signature', style: TextStyle(fontWeight: FontWeight.bold)),
                        Icon(Icons.draw, color: Colors.blue),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Container(
                      height: 180,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: Colors.grey.withValues(alpha: 0.05),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: _signatureCaptured ? Colors.green : Colors.grey),
                      ),
                      child: _signatureCaptured
                          ? Stack(
                              children: [
                                Center(child: Image.file(_signatureFile!)),
                                Positioned(
                                  top: 8,
                                  right: 8,
                                  child: IconButton(
                                    icon: const Icon(Icons.clear, color: Colors.red),
                                    onPressed: _clearSignature,
                                  ),
                                ),
                              ],
                            )
                          : SfSignaturePad(
                              key: _signaturePadKey,
                              backgroundColor: Colors.transparent,
                              strokeColor: Colors.black,
                              minimumStrokeWidth: 1.0,
                              maximumStrokeWidth: 4.0,
                            ),
                    ),
                    const SizedBox(height: 8),
                    if (!_signatureCaptured)
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          TextButton(
                            onPressed: () => _signaturePadKey.currentState?.clear(),
                            child: const Text('Clear', style: TextStyle(color: Colors.red)),
                          ),
                          ElevatedButton.icon(
                            onPressed: _saveSignature,
                            icon: const Icon(Icons.check),
                            label: const Text('Save Signature'),
                          ),
                        ],
                      ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Delivery Photo Capture Card
            Card(
              child: ListTile(
                leading: Icon(_photoCaptured ? Icons.check_circle : Icons.add_a_photo, color: _photoCaptured ? Colors.green : Colors.blue),
                title: const Text('Delivery Photo / Invoice Photo', style: TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text(_photoCaptured ? 'Photo Attached' : 'Tap to take delivery photo'),
                onTap: _capturePhoto,
              ),
            ),
            if (_photoFile != null)
              Padding(
                padding: const EdgeInsets.only(top: 8.0, left: 4, right: 4),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.file(_photoFile!, height: 150, width: double.infinity, fit: BoxFit.cover),
                ),
              ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _remarksController,
              maxLines: 3,
              decoration: const InputDecoration(labelText: 'Remarks / Delivery Notes', prefixIcon: Icon(Icons.note)),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isSubmitting ? null : _submitPod,
                child: _isSubmitting ? const CircularProgressIndicator() : const Text('Complete Trip & Submit POD'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
