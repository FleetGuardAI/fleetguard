import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'trip_intelligence_models.dart';

class TripIntelligenceRepository {
  final String baseUrl;

  TripIntelligenceRepository({this.baseUrl = 'http://10.0.2.2:10000'}); // Standard Android Emulator localhost

  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  Future<PreTripIntelligenceResponse> evaluateTripIntelligence(Map<String, dynamic> payload) async {
    final token = await _getToken();
    final response = await http.post(
      Uri.parse('$baseUrl/v1/trips/intelligence/evaluate'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode(payload),
    );

    if (response.statusCode == 200) {
      return PreTripIntelligenceResponse.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to evaluate trip intelligence: ${response.body}');
    }
  }

  Future<LiveTripIntelligenceResponse> getLiveTripIntelligence(int tripId) async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/v1/trips/$tripId/intelligence/live'),
      headers: {
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return LiveTripIntelligenceResponse.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to load live intelligence');
    }
  }

  Future<PostTripIntelligenceResponse> getTripIntelligence(int tripId) async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/v1/trips/$tripId/intelligence'),
      headers: {
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return PostTripIntelligenceResponse.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to load post-trip intelligence');
    }
  }
}
