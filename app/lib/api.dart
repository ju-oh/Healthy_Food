import 'dart:convert';

import 'package:http/http.dart' as http;

/// 에뮬레이터에서는 10.0.2.2가 PC의 localhost. 실제 폰은 --dart-define=API_BASE=http://PC의IP:8000
const apiBase = String.fromEnvironment('API_BASE', defaultValue: 'http://10.0.2.2:8000');

/// 지도 핀 캐릭터 종류
enum PinType { good, warn, plain }

class Shop {
  final String id, name, addr;
  final List<String> cuisines, violations;
  final double? lat, lng, distanceM;
  final bool graded;

  Shop.fromJson(Map<String, dynamic> j)
      : id = j['lcns_no'],
        name = j['name'],
        addr = j['addr'],
        cuisines = List<String>.from(j['cuisines']),
        violations = List<String>.from(j['violations']),
        lat = (j['lat'] as num?)?.toDouble(),
        lng = (j['lng'] as num?)?.toDouble(),
        distanceM = (j['distance_m'] as num?)?.toDouble(),
        graded = j['graded'];

  /// 위생 처분 공표 중이면 경고가 우선. 위생등급이 없는 건 '나쁨'이 아니라 '정보 없음'(자율 신청 제도)
  PinType get pin => violations.contains('hygiene')
      ? PinType.warn
      : graded
          ? PinType.good
          : PinType.plain;
}

Future<dynamic> _get(String path, [Map<String, String>? params]) async {
  final uri = Uri.parse(apiBase).replace(path: path, queryParameters: params);
  final res = await http.get(uri).timeout(const Duration(seconds: 10));
  if (res.statusCode != 200) throw Exception('API ${res.statusCode}: ${res.body}');
  return jsonDecode(utf8.decode(res.bodyBytes));
}

Future<List<Shop>> nearby(double lat, double lng, {String? cuisine, int radius = 2000}) async => [
      for (final j in await _get('/restaurants/nearby', {
        'lat': '$lat',
        'lng': '$lng',
        'radius': '$radius',
        'limit': '200',
        'cuisine': ?cuisine,
      }))
        Shop.fromJson(j)
    ];

Future<List<Shop>> search(String q) async =>
    [for (final j in await _get('/restaurants/search', {'q': q})) Shop.fromJson(j)];

/// 상세: Shop 필드 + grades, violation_details
Future<Map<String, dynamic>> detail(String id) async =>
    await _get('/restaurants/${Uri.encodeComponent(id)}');
