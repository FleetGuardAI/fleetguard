import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import '../providers/trip_providers.dart';
import '../../data/trip_repository.dart';
import '../../../../dashboard/presentation/providers/dashboard_providers.dart';

class TripDetailScreen extends ConsumerStatefulWidget {
  final int tripId;
  const TripDetailScreen({super.key, required this.tripId});

  @override
  ConsumerState<TripDetailScreen> createState() => _TripDetailScreenState();
}

class _TripDetailScreenState extends ConsumerState<TripDetailScreen> {
  bool _isLoading = false;

  Future<void> _startTripWithSelfie() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(
      source: ImageSource.camera,
      preferredCameraDevice: CameraDevice.front,
    );

    if (image == null) return;

    setState(() => _isLoading = true);
    try {
      final tripRepo = ref.read(tripRepositoryProvider);
      
      // Upload Selfie
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Uploading selfie...')));
      await tripRepo.uploadTripStartSelfie(widget.tripId, File(image.path));
      
      // Start Trip
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Starting trip...')));
      await tripRepo.startTrip(widget.tripId);
      
      ref.invalidate(todayTripsProvider);
      if (mounted) {
        context.push('/trip/${widget.tripId}/active');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tripAsync = ref.watch(singleTripProvider(widget.tripId.toString()));

    return Scaffold(
      appBar: AppBar(title: Text('Trip #TRIP-${widget.tripId}')),
      body: tripAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, stack) => Center(child: Text('Error: $err')),
        data: (trip) {
          final isCreated = trip['status'] == 'CREATED';
          final isInProgress = trip['status'] == 'IN_PROGRESS';
          
          return Stack(
            children: [
              SingleChildScrollView(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text('Customer Information', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                Icon(Icons.business, color: Colors.blue),
                              ],
                            ),
                            const Divider(height: 20),
                            Text('Company: ${trip['customer_name'] ?? 'Acme Logistics'}', style: const TextStyle(fontWeight: FontWeight.w600)),
                            Text('Contact: ${trip['customer_phone'] ?? '+91 98765 43210'}'),
                            const SizedBox(height: 8),
                            Text('Instructions: ${trip['instructions'] ?? 'Handle with care.'}', style: const TextStyle(color: Colors.grey)),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Route Info', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                            const SizedBox(height: 12),
                            ListTile(
                              leading: const Icon(Icons.my_location, color: Colors.green),
                              title: Text('Pickup: ${trip['origin_location']}'),
                            ),
                            ListTile(
                              leading: const Icon(Icons.location_on, color: Colors.red),
                              title: Text('Delivery: ${trip['destination_location']}'),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    Row(
                      children: [
                        if (isCreated)
                          Expanded(
                            child: ElevatedButton.icon(
                              onPressed: _startTripWithSelfie,
                              icon: const Icon(Icons.camera_alt),
                              label: const Text('Start Trip (Selfie)'),
                            ),
                          )
                        else if (isInProgress)
                          Expanded(
                            child: ElevatedButton.icon(
                              onPressed: () => context.push('/trip/${widget.tripId}/active'),
                              icon: const Icon(Icons.navigation),
                              label: const Text('Resume Navigation'),
                            ),
                          ),
                        if (isInProgress) const SizedBox(width: 12),
                        if (isInProgress)
                          OutlinedButton.icon(
                            onPressed: () => context.push('/pod/${widget.tripId}'),
                            icon: const Icon(Icons.assignment_turned_in),
                            label: const Text('Submit POD'),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              if (_isLoading)
                Container(
                  color: Colors.black45,
                  child: const Center(child: CircularProgressIndicator()),
                ),
            ],
          );
        },
      ),
    );
  }
}
