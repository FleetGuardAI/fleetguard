import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:dio/dio.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/network/api_client.dart';
import '../providers/fleet_provider.dart';
import '../../data/fleet_repository.dart';

class AddHardwareAssetScreen extends ConsumerStatefulWidget {
  const AddHardwareAssetScreen({super.key});

  @override
  ConsumerState<AddHardwareAssetScreen> createState() => _AddHardwareAssetScreenState();
}

class _AddHardwareAssetScreenState extends ConsumerState<AddHardwareAssetScreen> {
  final _formKey = GlobalKey<FormState>();
  final _apiKeyController = TextEditingController();
  final _deviceNameController = TextEditingController();
  final _vehicleSearchController = TextEditingController();
  
  bool _obscureApiKey = true;
  bool _isLoading = false;
  Vehicle? _selectedVehicle;

  @override
  void dispose() {
    _apiKeyController.dispose();
    _deviceNameController.dispose();
    _vehicleSearchController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedVehicle == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Please select a valid vehicle')));
      return;
    }

    setState(() => _isLoading = true);

    try {
      final dio = ref.read(apiClientProvider).dio;
      await dio.post('/api/v1/assets/hardware', data: {
        'api_key': _apiKeyController.text.trim(),
        'vehicle_id': _selectedVehicle!.id,
        'device_name': _deviceNameController.text.trim(),
      });
      
      ref.invalidate(hardwareAssetsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Hardware asset added successfully'), backgroundColor: AppColors.primary));
        context.pop();
      }
    } on DioException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.response?.data?['detail'] ?? 'Failed to add device'), backgroundColor: Colors.red));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Add Hardware Device'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Register New Device',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text(
                'Connect a new GPS tracker, dashcam, or telematics device to a vehicle in your fleet.',
                style: TextStyle(color: AppColors.coolGray),
              ),
              const SizedBox(height: 32),

              // API Key
              TextFormField(
                controller: _apiKeyController,
                obscureText: _obscureApiKey,
                decoration: InputDecoration(
                  labelText: 'API Key',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  prefixIcon: const Icon(Icons.key),
                  suffixIcon: IconButton(
                    icon: Icon(_obscureApiKey ? Icons.visibility_off : Icons.visibility),
                    onPressed: () => setState(() => _obscureApiKey = !_obscureApiKey),
                  ),
                ),
                validator: (val) => val == null || val.trim().isEmpty ? 'Required' : null,
              ),
              const SizedBox(height: 20),

              // Device Name
              TextFormField(
                controller: _deviceNameController,
                decoration: InputDecoration(
                  labelText: 'Device Name (e.g. Dashcam 3000)',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  prefixIcon: const Icon(Icons.memory),
                ),
                validator: (val) => val == null || val.trim().isEmpty ? 'Required' : null,
              ),
              const SizedBox(height: 20),

              // Vehicle Autocomplete
              Consumer(
                builder: (context, ref, child) {
                  final vehiclesAsync = ref.watch(vehiclesProvider);
                  return vehiclesAsync.when(
                    data: (vehicles) {
                      return Autocomplete<Vehicle>(
                        displayStringForOption: (Vehicle option) => '${option.licensePlate} - ${option.make} ${option.model}',
                        optionsBuilder: (TextEditingValue textEditingValue) {
                          if (textEditingValue.text.isEmpty) {
                            return const Iterable<Vehicle>.empty();
                          }
                          return vehicles.where((Vehicle option) {
                            return option.licensePlate.toLowerCase().contains(textEditingValue.text.toLowerCase()) || 
                                   option.make.toLowerCase().contains(textEditingValue.text.toLowerCase());
                          });
                        },
                        onSelected: (Vehicle selection) {
                          setState(() {
                            _selectedVehicle = selection;
                          });
                        },
                        fieldViewBuilder: (BuildContext context, TextEditingController fieldTextEditingController, FocusNode fieldFocusNode, VoidCallback onFieldSubmitted) {
                          return TextFormField(
                            controller: fieldTextEditingController,
                            focusNode: fieldFocusNode,
                            decoration: InputDecoration(
                              labelText: 'Assign to Vehicle (Type to search)',
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                              prefixIcon: const Icon(Icons.local_shipping),
                            ),
                            validator: (val) => _selectedVehicle == null ? 'Please select a valid vehicle from the list' : null,
                            onChanged: (val) {
                              if (_selectedVehicle != null) {
                                setState(() => _selectedVehicle = null);
                              }
                            },
                          );
                        },
                      );
                    },
                    loading: () => const Center(child: CircularProgressIndicator()),
                    error: (e, st) => const Text('Error loading vehicles'),
                  );
                },
              ),

              const SizedBox(height: 48),

              SizedBox(
                height: 56,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text('Connect Device', style: TextStyle(fontSize: 18, color: Colors.white, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
