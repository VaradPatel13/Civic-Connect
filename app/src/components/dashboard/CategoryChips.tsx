import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import categoriesData from '@src/data/categories.json';

export interface CategoryItem {
  id: string;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
}

const CATEGORIES: CategoryItem[] = categoriesData as CategoryItem[];

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
                size={16}
                color={isSelected ? '#059669' : '#64748B'}
              />
              <Text style={[styles.label, isSelected && styles.labelSelected]}>
                {cat.label}
              </Text>
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
});
