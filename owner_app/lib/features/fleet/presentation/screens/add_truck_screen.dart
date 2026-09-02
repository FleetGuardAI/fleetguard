import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../../../../core/theme/app_colors.dart';
import '../../data/fleet_repository.dart';
import '../providers/fleet_provider.dart';

class AddTruckScreen extends ConsumerStatefulWidget {
  const AddTruckScreen({super.key});

  @override
  ConsumerState<AddTruckScreen> createState() => _AddTruckScreenState();
}

class _AddTruckScreenState extends ConsumerState<AddTruckScreen> {
  bool _isScanning = false;
  bool _showVerification = false;
  final ImagePicker _picker = ImagePicker();

  final _regController = TextEditingController();
  final _manufacturerController = TextEditingController();
  final _modelController = TextEditingController();
  final _fuelTypeController = TextEditingController();
  final _gvwController = TextEditingController();

  @override
  void dispose() {
    _regController.dispose();
    _manufacturerController.dispose();
    _modelController.dispose();
    _fuelTypeController.dispose();
    _gvwController.dispose();
    super.dispose();
  }

  Future<void> _processImage(ImageSource source) async {
    try {
      final XFile? image = await _picker.pickImage(source: source);
      if (image == null) return;

      setState(() => _isScanning = true);

      final result = await ref.read(fleetRepositoryProvider).uploadRCForOCR(image.path);

      if (mounted) {
        setState(() {
          _regController.text = result['registration_number'] ?? '';
          _manufacturerController.text = result['manufacturer'] ?? '';
          _modelController.text = result['model'] ?? '';
          _fuelTypeController.text = result['fuel_type'] ?? '';
          _gvwController.text = result['gvw'] ?? '';
          
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

  void _submitTruck() async {
    if (_regController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Registration number is required')));
      return;
    }
    if (_manufacturerController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Manufacturer is required')));
      return;
    }

    try {
      final payload = {
        "license_plate": _regController.text.trim(),
        "make": _manufacturerController.text.trim(),
        if (_modelController.text.trim().isNotEmpty) "model": _modelController.text.trim(),
        "year": DateTime.now().year,
      };
      
      await ref.read(fleetRepositoryProvider).addVehicle(payload);
      // Invalidate the provider to refresh the list
      ref.invalidate(vehiclesProvider);
      if (mounted) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Truck added successfully')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error adding truck: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text('Add Truck', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        iconTheme: IconThemeData(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
        elevation: 1,
      ),
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
              borderRadius: BorderRadius.circular(16),
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
                        : const Icon(Icons.document_scanner, size: 64, color: AppColors.primary),
                    const SizedBox(height: 16),
                    Text(
                      _isScanning ? 'Extracting Data...' : 'Scan RC with Camera',
                      style: TextStyle(
                        fontSize: 20, 
                        fontWeight: FontWeight.bold,
                        color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface
                      ),
                    ),
                    if (!_isScanning)
                      Text('Automatically extract vehicle details', 
                        style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 32),
            Text('OR', style: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant, fontWeight: FontWeight.bold)),
            const SizedBox(height: 32),
            OutlinedButton.icon(
              onPressed: _isScanning ? null : () => _processImage(ImageSource.gallery),
              icon: const Icon(Icons.photo_library),
              label: const Text('Upload from Gallery'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.primary,
                side: const BorderSide(color: AppColors.primary),
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            )
          ],
        ),
      ),
    );
  }

  Widget _buildVerificationForm(bool isDark) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.primary.withValues(alpha: 0.3)),
            ),
            child: Row(
              children: [
                const Icon(Icons.check_circle, color: AppColors.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Data extracted successfully. Please verify and correct if needed.',
                    style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          _buildTextField('Vehicle Registration', _regController, isDark, Icons.pin),
          const SizedBox(height: 16),
          _buildTextField('Manufacturer', _manufacturerController, isDark, Icons.business),
          const SizedBox(height: 16),
          _buildTextField('Model', _modelController, isDark, Icons.local_shipping),
          const SizedBox(height: 16),
          _buildTextField('Fuel Type', _fuelTypeController, isDark, Icons.local_gas_station),
          const SizedBox(height: 16),
          _buildTextField('GVW', _gvwController, isDark, Icons.monitor_weight),
          const SizedBox(height: 32),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              elevation: 2,
            ),
            onPressed: _submitTruck,
            child: const Text('Confirm & Add Truck', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          ),
          const SizedBox(height: 16),
          TextButton(
            onPressed: () {
              setState(() {
                _showVerification = false;
              });
            },
            child: const Text('Scan Again'),
          )
        ],
      ),
    );
  }

  Widget _buildTextField(String label, TextEditingController controller, bool isDark, IconData icon) {
    return TextField(
      controller: controller,
      style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: TextStyle(color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
        prefixIcon: Icon(icon, color: isDark ? AppColors.darkOnSurfaceVariant : AppColors.lightOnSurfaceVariant),
        filled: true,
        fillColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.primary, width: 2),
        ),
      ),
    );
  }
}
