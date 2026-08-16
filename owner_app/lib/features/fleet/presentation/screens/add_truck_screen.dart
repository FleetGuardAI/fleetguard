import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

class AddTruckScreen extends StatefulWidget {
  const AddTruckScreen({super.key});

  @override
  State<AddTruckScreen> createState() => _AddTruckScreenState();
}

class _AddTruckScreenState extends State<AddTruckScreen> {
  bool _isScanning = false;
  bool _showVerification = false;

  final _regController = TextEditingController(text: 'UK07AB1234');
  final _manufacturerController = TextEditingController(text: 'Tata Motors');
  final _modelController = TextEditingController(text: 'Prima');
  final _fuelTypeController = TextEditingController(text: 'Diesel');
  final _gvwController = TextEditingController(text: '55,000 kg');

  void _simulateScan() async {
    setState(() => _isScanning = true);
    await Future.delayed(const Duration(seconds: 2));
    setState(() {
      _isScanning = false;
      _showVerification = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundCream,
      appBar: AppBar(title: const Text('Add Truck')),
      body: _showVerification ? _buildVerificationForm() : _buildScanOptions(),
    );
  }

  Widget _buildScanOptions() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            InkWell(
              onTap: _isScanning ? null : _simulateScan,
              child: Container(
                padding: const EdgeInsets.all(32),
                decoration: BoxDecoration(
                  color: AppTheme.cardLight,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppTheme.primaryGreen, width: 2),
                ),
                child: Column(
                  children: [
                    _isScanning 
                        ? const CircularProgressIndicator(color: AppTheme.primaryGreen) 
                        : const Icon(Icons.document_scanner, size: 64, color: AppTheme.primaryGreen),
                    const SizedBox(height: 16),
                    Text(
                      _isScanning ? 'Processing OCR...' : 'Scan RC',
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    if (!_isScanning)
                      const Text('Scan vehicle RC', style: TextStyle(color: AppTheme.textSecondary)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            const Text('OR'),
            const SizedBox(height: 24),
            TextButton.icon(
              onPressed: _simulateScan,
              icon: const Icon(Icons.photo_library),
              label: const Text('Upload from Gallery'),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildVerificationForm() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Verify Extracted Information', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          _buildTextField('Vehicle Registration', _regController),
          const SizedBox(height: 12),
          _buildTextField('Manufacturer', _manufacturerController),
          const SizedBox(height: 12),
          _buildTextField('Model', _modelController),
          const SizedBox(height: 12),
          _buildTextField('Fuel Type', _fuelTypeController),
          const SizedBox(height: 12),
          _buildTextField('GVW', _gvwController),
          const SizedBox(height: 32),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryGreen,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () {
              Navigator.pop(context);
            },
            child: const Text('Confirm & Add Truck', style: TextStyle(fontSize: 16, color: Colors.white)),
          )
        ],
      ),
    );
  }

  Widget _buildTextField(String label, TextEditingController controller) {
    return TextField(
      controller: controller,
      decoration: InputDecoration(
        labelText: label,
        filled: true,
        fillColor: AppTheme.cardLight,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
      ),
    );
  }
}
