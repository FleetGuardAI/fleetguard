import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';
import '../providers/trip_providers.dart';
import '../../data/trip_repository.dart';
import '../../../dashboard/presentation/providers/dashboard_providers.dart';

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
                            Text('Company: ${trip['customer_name'] ?? 'Not provided'}', style: const TextStyle(fontWeight: FontWeight.w600)),
                            if (trip['customer_phone'] != null) Text('Contact: ${trip['customer_phone']}'),
                            const SizedBox(height: 8),
                            if (trip['instructions'] != null) Text('Instructions: ${trip['instructions']}', style: const TextStyle(color: Colors.grey)),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    // Receiver Information Card
                    if (trip['receiver_name'] != null || trip['receiver_phone'] != null || trip['receiver_address'] != null)
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Text('Receiver Information', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                  Icon(Icons.person, color: Colors.blue),
                                ],
                              ),
                              const Divider(height: 20),
                              if (trip['receiver_name'] != null) Text('Name: ${trip['receiver_name']}', style: const TextStyle(fontWeight: FontWeight.w600)),
                              if (trip['receiver_phone'] != null) Text('Phone: ${trip['receiver_phone']}'),
                              if (trip['receiver_company'] != null) Text('Company: ${trip['receiver_company']}'),
                              if (trip['receiver_address'] != null) Text('Address: ${trip['receiver_address']}, ${trip['receiver_city']}, ${trip['receiver_state'] ?? ''} - ${trip['receiver_pincode']}'),
                              if (trip['receiver_notes'] != null) Text('Notes: ${trip['receiver_notes']}', style: const TextStyle(color: Colors.grey)),
                              const SizedBox(height: 12),
                              Row(
                                children: [
                                  if (trip['receiver_phone'] != null)
                                    Expanded(
                                      child: OutlinedButton.icon(
                                        onPressed: () async {
                                          final url = Uri.parse('tel:${trip['receiver_phone']}');
                                          if (await canLaunchUrl(url)) {
                                            await launchUrl(url);
                                          }
                                        },
                                        icon: const Icon(Icons.phone),
                                        label: const Text('Call'),
                                      ),
                                    ),
                                  if (trip['receiver_phone'] != null) const SizedBox(width: 8),
                                  if (trip['destination_lat'] != null && trip['destination_lng'] != null)
                                    Expanded(
                                      child: OutlinedButton.icon(
                                        onPressed: () async {
                                          final url = Uri.parse('https://www.google.com/maps/search/?api=1&query=${trip['destination_lat']},${trip['destination_lng']}');
                                          if (await canLaunchUrl(url)) {
                                            await launchUrl(url, mode: LaunchMode.externalApplication);
                                          }
                                        },
                                        icon: const Icon(Icons.navigation),
                                        label: const Text('Navigate'),
                                      ),
                                    ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    const SizedBox(height: 16),
                    Card(
                      elevation: 2,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text('Approved Route', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: (trip['route_status'] == 'DEVIATION_SUSPECTED' || trip['route_status'] == 'DEVIATION_CONFIRMED')
                                        ? Colors.orange.shade100
                                        : Colors.green.shade100,
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    trip['route_status'] ?? 'APPROVED',
                                    style: TextStyle(
                                      color: (trip['route_status'] == 'DEVIATION_SUSPECTED' || trip['route_status'] == 'DEVIATION_CONFIRMED')
                                          ? Colors.orange.shade900
                                          : Colors.green.shade900,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 12,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const Divider(height: 20),
                            ListTile(
                              dense: true,
                              contentPadding: EdgeInsets.zero,
                              leading: const Icon(Icons.trip_origin, color: Colors.green),
                              title: const Text('Pickup', style: TextStyle(fontSize: 12, color: Colors.grey)),
                              subtitle: Text(trip['origin_location'] ?? 'Not specified', style: const TextStyle(fontWeight: FontWeight.w600)),
                            ),
                            ListTile(
                              dense: true,
                              contentPadding: EdgeInsets.zero,
                              leading: const Icon(Icons.location_on, color: Colors.red),
                              title: const Text('Delivery', style: TextStyle(fontSize: 12, color: Colors.grey)),
                              subtitle: Text(trip['destination_location'] ?? 'Not specified', style: const TextStyle(fontWeight: FontWeight.w600)),
                            ),
                            const Divider(height: 16),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceAround,
                              children: [
                                Column(
                                  children: [
                                    const Text('Distance', style: TextStyle(fontSize: 12, color: Colors.grey)),
                                    const SizedBox(height: 4),
                                    Text(
                                      trip['route_distance_km'] != null
                                          ? '${trip['route_distance_km']} km'
                                          : (trip['total_distance_km'] != null ? '${trip['total_distance_km']} km' : '--'),
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                                    ),
                                  ],
                                ),
                                Column(
                                  children: [
                                    const Text('Est. Duration', style: TextStyle(fontSize: 12, color: Colors.grey)),
                                    const SizedBox(height: 4),
                                    Text(
                                      trip['route_duration_hours'] != null
                                          ? '${(trip['route_duration_hours'] * 60).round()} min'
                                          : (trip['eta_minutes'] != null ? '${trip['eta_minutes']} min' : '--'),
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                                    ),
                                  ],
                                ),
                                Column(
                                  children: [
                                    const Text('Toll Estimate', style: TextStyle(fontSize: 12, color: Colors.grey)),
                                    const SizedBox(height: 4),
                                    Text(
                                      trip['route_toll_estimate'] != null
                                          ? '₹${trip['route_toll_estimate']}'
                                          : 'N/A',
                                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Colors.teal),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: Colors.blueGrey.shade50,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Row(
                                children: [
                                  Icon(Icons.info_outline, size: 16, color: Colors.blueGrey),
                                  SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      'Heavy commercial route approved. Follow mandatory highway restrictions.',
                                      style: TextStyle(fontSize: 11, color: Colors.blueGrey),
                                    ),
                                  ),
                                ],
                              ),
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
