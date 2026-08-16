import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// Injectable image providers for mock data. 
// This allows widget tests to override these with local/memory images
// and avoid HTTP requests.

final mockAvatarProvider = Provider<ImageProvider>((ref) {
  return const NetworkImage('https://i.pravatar.cc/150?u=suryansh');
});

final mockMapProvider = Provider<ImageProvider>((ref) {
  return const NetworkImage('https://maps.googleapis.com/maps/api/staticmap?center=28.6139,77.2090&zoom=10&size=600x300&maptype=roadmap');
});
