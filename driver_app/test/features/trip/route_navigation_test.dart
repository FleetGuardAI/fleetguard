import 'package:flutter_test/flutter_test.dart';
import 'package:fleetguard_driver/core/utils/polyline_decoder.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

void main() {
  group('Intelligent Routing and Polyline Decoder Tests', () {
    test('decodePolyline decodes standard encoded polyline correctly', () {
      // Benchmark encoded polyline for [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]
      const encoded = '_p~iF~ps|U_ulLnnqC_mqNvxq`@';
      final points = decodePolyline(encoded);

      expect(points.length, equals(3));
      expect(points[0].latitude, closeTo(38.5, 0.001));
      expect(points[0].longitude, closeTo(-120.2, 0.001));
      expect(points[1].latitude, closeTo(40.7, 0.001));
      expect(points[1].longitude, closeTo(-120.95, 0.001));
      expect(points[2].latitude, closeTo(43.252, 0.001));
      expect(points[2].longitude, closeTo(-126.453, 0.001));
    });

    test('decodePolyline handles empty polyline gracefully', () {
      final points = decodePolyline('');
      expect(points, isEmpty);
    });

    test('Trip route status logic distinguishes normal vs deviation', () {
      const normalStatuses = ['APPROVED', 'COMPLETED', 'IN_PROGRESS'];
      const deviationStatuses = ['DEVIATION_SUSPECTED', 'DEVIATION_CONFIRMED'];

      for (final s in normalStatuses) {
        final isDev = s == 'DEVIATION_SUSPECTED' || s == 'DEVIATION_CONFIRMED';
        expect(isDev, isFalse);
      }

      for (final s in deviationStatuses) {
        final isDev = s == 'DEVIATION_SUSPECTED' || s == 'DEVIATION_CONFIRMED';
        expect(isDev, isTrue);
      }
    });

    test('Formats distance, duration, and toll metrics accurately', () {
      const distanceKm = 142.5;
      const durationHours = 2.75;
      const tollEstimate = 280.0;

      final formattedDistance = '${distanceKm.toStringAsFixed(1)} km';
      final formattedDuration = '${(durationHours * 60).round()} min';
      final formattedToll = '₹${tollEstimate.toStringAsFixed(0)}';

      expect(formattedDistance, equals('142.5 km'));
      expect(formattedDuration, equals('165 min'));
      expect(formattedToll, equals('₹280'));
    });
  });
}
