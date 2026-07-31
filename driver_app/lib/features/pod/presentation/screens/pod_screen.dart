import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class PodScreen extends StatefulWidget {
  final int tripId;

  const PodScreen({super.key, required this.tripId});

  @override
  State<PodScreen> createState() => _PodScreenState();
}

class _PodScreenState extends State<PodScreen> {
  final _remarksController = TextEditingController();
  final _receiverController = TextEditingController();

  bool _signatureCaptured = false;
  bool _photoCaptured = false;
  bool _isSubmitting = false;

  void _submitPod() async {
    if (!_signatureCaptured) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please capture customer signature first')),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    await Future.delayed(const Duration(seconds: 1));
    setState(() => _isSubmitting = false);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Proof of Delivery (POD) submitted. Trip completed!')),
      );
      context.go('/dashboard');
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
                      height: 140,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: Colors.grey.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.grey),
                      ),
                      child: Center(
                        child: _signatureCaptured
                            ? const Icon(Icons.gesture, size: 80, color: Colors.blue)
                            : const Text('Touch / Draw Signature Here', style: TextStyle(color: Colors.grey)),
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextButton.icon(
                      onPressed: () => setState(() => _signatureCaptured = true),
                      icon: const Icon(Icons.check),
                      label: Text(_signatureCaptured ? 'Signature Captured' : 'Capture Digital Signature'),
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
                onTap: () => setState(() => _photoCaptured = true),
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
