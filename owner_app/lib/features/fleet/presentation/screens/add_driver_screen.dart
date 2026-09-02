import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../../../core/theme/app_colors.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/fleet_repository.dart';
import '../providers/fleet_provider.dart';

class AddDriverScreen extends ConsumerStatefulWidget {
  const AddDriverScreen({super.key});

  @override
  ConsumerState<AddDriverScreen> createState() => _AddDriverScreenState();
}

class _AddDriverScreenState extends ConsumerState<AddDriverScreen> {
  bool _isScanning = false;
  bool _showVerification = false;
  final ImagePicker _picker = ImagePicker();

  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _licenseController = TextEditingController();
  final _dobController = TextEditingController();
  final _validUntilController = TextEditingController();
  final _classController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _licenseController.dispose();
    _dobController.dispose();
    _validUntilController.dispose();
    _classController.dispose();
    super.dispose();
  }

  Future<void> _processImage(ImageSource source) async {
    try {
      final XFile? image = await _picker.pickImage(source: source);
      if (image == null) return;

      setState(() => _isScanning = true);

      final result = await ref.read(fleetRepositoryProvider).uploadLicenseForOCR(image.path);

      if (mounted) {
        setState(() {
          _nameController.text = result['name'] ?? '';
          _licenseController.text = result['license_number'] ?? '';
          _dobController.text = result['date_of_birth'] ?? '';
          _validUntilController.text = result['valid_until'] ?? '';
          _classController.text = result['vehicle_class'] ?? '';
          
          _isScanning = false;
          _showVerification = true;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isScanning = false);
        
        String errorMsg = 'Could not read document. Please try a clearer image.';
        if (e.toString().contains('timeout') || e.toString().contains('Timeout')) {
          errorMsg = 'Network timeout. Please check your connection.';
        }
        
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(errorMsg),
          backgroundColor: AppColors.statusRed,
          duration: const Duration(seconds: 5),
        ));
      }
    }
  }

  void _submitDriver() async {
    try {
      await ref.read(fleetRepositoryProvider).addDriver({
        "name": _nameController.text,
        "phone_number": _phoneController.text,
        "license_number": _licenseController.text,
      });
      ref.invalidate(driversProvider);
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Driver added successfully')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error adding driver: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(title: Text('Add Driver', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface))),
      body: _showVerification ? _buildVerificationForm(isDark) : _buildScanOptions(isDark),
    );
  }

  Widget _buildScanOptions(bool isDark) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            InkWell(
              onTap: _isScanning ? null : () => _processImage(ImageSource.camera),
              child: Container(
                padding: const EdgeInsets.all(32),
                decoration: BoxDecoration(
                  color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.primary, width: 2),
                ),
                child: Column(
                  children: [
                    _isScanning 
                        ? const CircularProgressIndicator(color: AppColors.primary) 
                        : const Icon(Icons.camera_alt, size: 64, color: AppColors.primary),
                    const SizedBox(height: 16),
                    Text(
                      _isScanning ? 'Processing OCR...' : 'Scan License',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
                    ),
                    if (!_isScanning)
                      Text('Scan driver\'s license', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.coolGray)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text('OR', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
            const SizedBox(height: 24),
            TextButton.icon(
              onPressed: _isScanning ? null : () => _processImage(ImageSource.gallery),
              icon: Icon(Icons.photo_library, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
              label: Text('Upload from Gallery', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildVerificationForm(bool isDark) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('Verify Extracted Information', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
          const SizedBox(height: 16),
          _buildTextField('Name', _nameController, isDark),
          const SizedBox(height: 12),
          _buildTextField('Phone Number', _phoneController, isDark),
          const SizedBox(height: 12),
          _buildTextField('License Number', _licenseController, isDark),
          const SizedBox(height: 12),
          _buildTextField('Date of Birth', _dobController, isDark),
          const SizedBox(height: 12),
          _buildTextField('Valid Until', _validUntilController, isDark),
          const SizedBox(height: 12),
          _buildTextField('Vehicle Class', _classController, isDark),
          const SizedBox(height: 32),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: _submitDriver,
            child: const Text('Confirm & Add Driver', style: TextStyle(fontSize: 16, color: Colors.white)),
          )
        ],
      ),
    );
  }

  Widget _buildTextField(String label, TextEditingController controller, bool isDark) {
    return TextField(
      controller: controller,
      style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
        filled: true,
        fillColor: isDark ? AppColors.darkInputFill : AppColors.lightInputFill,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
      ),
    );
  }
}
