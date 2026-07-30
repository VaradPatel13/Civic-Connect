import { useEffect, useRef, useState } from 'react';
import {
  Dimensions,
  FlatList,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const { width: SCREEN_W } = Dimensions.get('window');
const H_PAD = 20;

export interface AnnouncementSlide {
  id: string;
  badge: string;
  title: string;
  sub: string;
  colorBg: string;
  accentColor: string;
  icon: keyof typeof Ionicons.glyphMap;
}

const DEFAULT_SLIDES: AnnouncementSlide[] = [
  {
    id: 'slide-1',
    badge: 'MUNICIPAL DRIVE',
    title: 'Clean Ward 12 & Zero Waste Drive 2026',
    sub: 'Join 1,200+ citizens segregating waste & planting 500 native trees.',
    colorBg: '#064E3B',
    accentColor: '#34D399',
    icon: 'leaf-outline',
  },
  {
    id: 'slide-2',
    badge: 'INFRASTRUCTURE UPDATE',
    title: '100% Solar Streetlights on Main Arterial Roads',
    sub: 'Smart LED grids installed across University Road & FC Road junction.',
    colorBg: '#047857',
    accentColor: '#84CC16',
    icon: 'flash-outline',
  },
  {
    id: 'slide-3',
    badge: 'MONSOON PREPAREDNESS',
    title: 'High-Capacity Drainage Cleaning Drive',
    sub: 'PMC engineering teams clearing 45km stormwater drains ahead of monsoon.',
    colorBg: '#065F46',
    accentColor: '#06B6D4',
    icon: 'water-outline',
  },
];

interface AnnouncementCarouselProps {
  slides?: AnnouncementSlide[];
}

export function AnnouncementCarousel({ slides = DEFAULT_SLIDES }: AnnouncementCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);
  const slideWidth = SCREEN_W - H_PAD * 2;

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveIndex((prev) => {
        const next = (prev + 1) % slides.length;
        flatListRef.current?.scrollToIndex({ index: next, animated: true });
        return next;
      });
    }, 4500);
    return () => clearInterval(timer);
  }, [slides.length]);

  return (
    <View style={styles.container}>
      <FlatList
        ref={flatListRef}
        data={slides}
        keyExtractor={(item) => item.id}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(ev) => {
          const newIdx = Math.round(ev.nativeEvent.contentOffset.x / slideWidth);
          setActiveIndex(newIdx);
        }}
        renderItem={({ item }) => (
          <View style={[styles.slideCard, { width: slideWidth, backgroundColor: item.colorBg }]}>
            <View style={styles.badgeRow}>
              <Ionicons name={item.icon} size={12} color={item.accentColor} />
              <Text style={[styles.badgeText, { color: item.accentColor }]}>{item.badge}</Text>
            </View>
            <Text style={styles.title} numberOfLines={1}>{item.title}</Text>
            <Text style={styles.subtitle} numberOfLines={2}>{item.sub}</Text>
          </View>
        )}
      />

      <View style={styles.dotsRow}>
        {slides.map((_, i) => (
          <View
            key={i}
            style={[
              styles.dot,
              {
                backgroundColor: i === activeIndex ? '#059669' : '#CBD5E1',
                width: i === activeIndex ? 18 : 6,
              },
            ]}
          />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 4,
  },
  slideCard: {
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 16,
    gap: 6,
    minHeight: 110,
    justifyContent: 'center',
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: -0.3,
  },
  subtitle: {
    color: 'rgba(255, 255, 255, 0.85)',
    fontSize: 12,
    lineHeight: 16,
  },
  dotsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 8,
  },
  dot: {
    height: 6,
    borderRadius: 3,
  },
});
