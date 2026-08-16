import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

class AddDriverScreen extends StatefulWidget {
  const AddDriverScreen({super.key});

  @override
  State<AddDriverScreen> createState() => _AddDriverScreenState();
}

class _AddDriverScreenState extends State<AddDriverScreen> {
  bool _isScanning = false;
  bool _showVerification = false;

  final _nameController = TextEditingController(text: 'Ravi Kumar');
  final _licenseController = TextEditingController(text: 'UK0123456789');
  final _dobController = TextEditingController(text: '12/04/1998');
  final _validUntilController = TextEditingController(text: '12/04/2028');
  final _classController = TextEditingController(text: 'HMV');

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
      appBar: AppBar(title: const Text('Add Driver')),
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
                        : const Icon(Icons.camera_alt, size: 64, color: AppTheme.primaryGreen),
                    const SizedBox(height: 16),
                    Text(
                      _isScanning ? 'Processing OCR...' : 'Scan License',
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    if (!_isScanning)
                      const Text('Scan driver\'s license', style: TextStyle(color: AppTheme.textSecondary)),
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
          _buildTextField('Name', _nameController),
          const SizedBox(height: 12),
          _buildTextField('License Number', _licenseController),
          const SizedBox(height: 12),
          _buildTextField('Date of Birth', _dobController),
          const SizedBox(height: 12),
          _buildTextField('Valid Until', _validUntilController),
          const SizedBox(height: 12),
          _buildTextField('Vehicle Class', _classController),
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
            child: const Text('Confirm & Add Driver', style: TextStyle(fontSize: 16, color: Colors.white)),
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
