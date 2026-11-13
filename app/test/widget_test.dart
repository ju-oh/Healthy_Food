import 'package:flutter_test/flutter_test.dart';
import 'package:healthy_food/api.dart';

Map<String, dynamic> shop({bool graded = false, List<String> violations = const []}) => {
      'lcns_no': '1',
      'name': '교촌치킨',
      'addr': '부산',
      'cuisines': ['치킨'],
      'violations': violations,
      'lat': 35.1,
      'lng': 129,
      'graded': graded,
    };

void main() {
  test('핀 종류: 위생 처분이 위생등급보다 우선, 등급 없음은 경고가 아님', () {
    expect(Shop.fromJson(shop(graded: true)).pin, PinType.good);
    expect(Shop.fromJson(shop(graded: true, violations: ['hygiene'])).pin, PinType.warn);
    expect(Shop.fromJson(shop(violations: ['conduct'])).pin, PinType.plain);
    expect(Shop.fromJson(shop()).pin, PinType.plain);
  });

  test('좌표·거리 없는 응답도 읽는다', () {
    final s = Shop.fromJson({...shop(), 'lat': null, 'lng': null});
    expect(s.lat, isNull);
    expect(s.distanceM, isNull);
    expect(Shop.fromJson({...shop(), 'distance_m': 122}).distanceM, 122.0);
  });
}
