import 'package:flutter_test/flutter_test.dart';
import 'package:fleetguard_owner/core/utils/polyline_decoder.dart';
import 'package:fleetguard_owner/features/trip/data/trip_repository.dart';

void main() {
  group('Owner App Route Intelligence and Tracking Tests', () {
    test('decodePolyline decodes multi-segment geometry', () {
      const encoded = '_p~iF~ps|U_ulLnnqC_mqNvxq`@';
      final points = decodePolyline(encoded);

      expect(points.length, equals(3));
      expect(points[0].latitude, closeTo(38.5, 0.001));
      expect(points[0].longitude, closeTo(-120.2, 0.001));
    });

    test('OwnerTrip parses routing intelligence and deviation attributes', () {
      final json = {
        'id': 101,
        'trip_id': 'TRIP-101',
        'status': 'IN_PROGRESS',
        'origin_location': 'Delhi Warehouse 1',
        'destination_location': 'Jaipur Logistics Hub',
        'origin_lat': 28.6139,
        'origin_lng': 77.2090,
        'destination_lat': 26.9124,
        'destination_lng': 75.7873,
        'route_polyline': '_p~iF~ps|U_ulLnnqC',
        'route_status': 'DEVIATION_CONFIRMED',
        'route_distance_km': 268.4,
        'route_duration_hours': 4.8,
        'route_toll_estimate': 450.0,
        'approved_route_version_id': 2,
      };

      final trip = OwnerTrip.fromJson(json);

      expect(trip.id, equals(101));
      expect(trip.tripId, equals('TRIP-101'));
      expect(trip.status, equals('IN_PROGRESS'));
      expect(trip.routeStatus, equals('DEVIATION_CONFIRMED'));
      expect(trip.routeDistanceKm, equals(268.4));
      expect(trip.routeDurationHours, equals(4.8));
      expect(trip.routeTollEstimate, equals(450.0));
      expect(trip.approvedRouteVersionId, equals(2));
      expect(trip.originLat, equals(28.6139));
      expect(trip.destinationLat, equals(26.9124));
    });
  });
}
