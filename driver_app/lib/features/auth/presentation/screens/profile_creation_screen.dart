import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/storage/secure_storage.dart';
import '../../../../core/utils/validators.dart';
import '../../data/auth_repository.dart';

class ProfileCreationScreen extends ConsumerStatefulWidget {
  const ProfileCreationScreen({super.key});

  @override
  ConsumerState<ProfileCreationScreen> createState() => _ProfileCreationScreenState();
}

class _ProfileCreationScreenState extends ConsumerState<ProfileCreationScreen> {
  final _nameController = TextEditingController();
  final _licenseController = TextEditingController();
  final _aadhaarController = TextEditingController();
  final _ageController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isLoading = false;

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    
    try {
      final repo = ref.read(authRepositoryProvider);
      final age = int.tryParse(_ageController.text.trim()) ?? 0;
      final response = await repo.registerProfile(
        _nameController.text.trim(),
        _licenseController.text.trim(),
        _aadhaarController.text.trim(),
        age,
      );

      await SecureStorage.setDriverName(response['name']);
      
      setState(() => _isLoading = false);

      if (mounted) {
        context.go('/auth/documents');
      }
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to update profile: $e'), backgroundColor: Theme.of(context).colorScheme.error),
        );
      }
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _licenseController.dispose();
    _aadhaarController.dispose();
    _ageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Driver Profile')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Personal Information',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text('Enter your details exactly as they appear on your driving license.'),
              const SizedBox(height: 24),
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Full Name',
                  prefixIcon: Icon(Icons.person),
                ),
                validator: Validators.name,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _ageController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Age',
                  prefixIcon: Icon(Icons.cake),
                  hintText: '18 - 80',
                ),
                validator: (v) {
                  if (v == null || v.trim().isEmpty) return 'Age is required';
                  final age = int.tryParse(v.trim());
                  if (age == null || age < 18 || age > 80) {
                    return 'Enter a valid age between 18 and 80';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _licenseController,
                decoration: const InputDecoration(
                  labelText: 'Driving License Number',
                  prefixIcon: Icon(Icons.badge),
                ),
                validator: Validators.licenseNumber,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _aadhaarController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Aadhaar Number',
                  prefixIcon: Icon(Icons.fingerprint),
                ),
                validator: (v) => Validators.required(v, 'Aadhaar'),
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _submit,
                  child: _isLoading ? const CircularProgressIndicator() : const Text('Next: Upload Documents'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
