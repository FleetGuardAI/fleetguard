import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/storage/secure_storage.dart';
import '../../../../core/utils/validators.dart';

class ProfileCreationScreen extends StatefulWidget {
  const ProfileCreationScreen({super.key});

  @override
  State<ProfileCreationScreen> createState() => _ProfileCreationScreenState();
}

class _ProfileCreationScreenState extends State<ProfileCreationScreen> {
  final _nameController = TextEditingController();
  final _licenseController = TextEditingController();
  final _aadhaarController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _isLoading = false;

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 1));

    await SecureStorage.setDriverName(_nameController.text.trim());
    setState(() => _isLoading = false);

    if (mounted) {
      context.go('/auth/documents');
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _licenseController.dispose();
    _aadhaarController.dispose();
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
