import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

export interface CategoryItem {
  id: string;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  count: number;
}

const CATEGORIES: CategoryItem[] = [
  { id: 'pothole', label: 'Potholes & Roads', icon: 'construct-outline', count: 12 },
  { id: 'streetlight', label: 'Street Lights', icon: 'flash-outline', count: 8 },
  { id: 'drainage', label: 'Water & Drainage', icon: 'water-outline', count: 6 },
  { id: 'sanitation', label: 'Waste Disposal', icon: 'trash-bin-outline', count: 5 },
  { id: 'traffic', label: 'Traffic Signals', icon: 'navigate-outline', count: 3 },
];

interface CategoryChipsProps {
  selectedCategory: string | null;
  onSelectCategory: (id: string | null) => void;
}

export function CategoryChips({ selectedCategory, onSelectCategory }: CategoryChipsProps) {
  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.sectionTitle}>Trending Categories</Text>
        {selectedCategory ? (
          <TouchableOpacity
            onPress={() => {
              Haptics.selectionAsync();
              onSelectCategory(null);
            }}
          >
            <Text style={styles.resetText}>Show All</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {CATEGORIES.map((cat) => {
          const isSelected = selectedCategory === cat.id;
          return (
            <TouchableOpacity
              key={cat.id}
              activeOpacity={0.7}
              style={[styles.chip, isSelected && styles.chipSelected]}
              onPress={() => {
                Haptics.selectionAsync();
                onSelectCategory(isSelected ? null : cat.id);
              }}
            >
              <Ionicons
                name={cat.icon}
                size={15}
                color={isSelected ? '#059669' : '#64748B'}
              />
              <Text style={[styles.label, isSelected && styles.labelSelected]}>
                {cat.label}
              </Text>
              <View style={[styles.badge, isSelected && styles.badgeSelected]}>
                <Text style={[styles.badgeText, isSelected && styles.badgeTextSelected]}>
                  {cat.count}
                </Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 10,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0F172A',
    letterSpacing: -0.3,
  },
  resetText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#059669',
  },
  scrollContent: {
    gap: 8,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 8,
    paddingVertical: 7,
    paddingHorizontal: 12,
  },
  chipSelected: {
    backgroundColor: '#ECFDF5',
    borderColor: '#059669',
  },
  label: {
    fontSize: 13,
    fontWeight: '500',
    color: '#334155',
  },
  labelSelected: {
    fontWeight: '600',
    color: '#059669',
  },
  badge: {
    backgroundColor: '#F1F5F9',
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 1,
  },
  badgeSelected: {
    backgroundColor: '#A7F3D0',
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#64748B',
  },
  badgeTextSelected: {
    color: '#065F46',
  },
});
