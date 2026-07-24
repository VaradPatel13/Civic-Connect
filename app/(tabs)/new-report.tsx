import React, { useState } from 'react';
import { StyleSheet, Text, View, TextInput, Alert, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { reportService } from '../services';

const CATEGORIES = ['roads', 'water', 'garbage', 'electricity', 'sewage', 'parks', 'traffic', 'other'];

export default function NewReportScreen() {
  const router = useRouter();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('roads');
  const [urgency, setUrgency] = useState('medium');
  const [address, setAddress] = useState('FC Road, Pune');
  const [photoUrl, setPhotoUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!title || !description) {
      Alert.alert('Required Fields', 'Please enter a title and description.');
      return;
    }
    setLoading(true);
    try {
      await reportService.createReport({
        title,
        description,
        issue_category: category,
        urgency,
        latitude: 18.5204,
        longitude: 73.8567,
        address,
        photos: photoUrl ? [photoUrl] : ['https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?w=600'],
      });
      Alert.alert('Success', 'Civic issue report submitted! Assigned to PMC AI Routing.', [
        { text: 'OK', onPress: () => router.replace('/(tabs)/reports') },
      ]);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Report submission failed.';
      Alert.alert('Submission Error', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Card style={styles.card}>
        <Text style={styles.cardTitle}>Submit New Civic Issue</Text>

        <Text style={styles.label}>Issue Title *</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. Severe Pothole near FC Road"
          placeholderTextColor="#64748b"
          value={title}
          onChangeText={setTitle}
        />

        <Text style={styles.label}>Select Category *</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipRow}>
          {CATEGORIES.map((cat) => (
            <TouchableOpacity
              key={cat}
              style={[styles.chip, category === cat && styles.chipActive]}
              onPress={() => setCategory(cat)}
            >
              <Text style={[styles.chipText, category === cat && styles.chipTextActive]}>
                {cat.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <Text style={styles.label}>Description *</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Describe the issue, landmarks, and severity..."
          placeholderTextColor="#64748b"
          multiline
          numberOfLines={4}
          value={description}
          onChangeText={setDescription}
        />

        <Text style={styles.label}>Location / Address</Text>
        <TextInput
          style={styles.input}
          placeholder="Street address, PMC Ward Number"
          placeholderTextColor="#64748b"
          value={address}
          onChangeText={setAddress}
        />

        <Text style={styles.label}>Photo URL (Optional)</Text>
        <TextInput
          style={styles.input}
          placeholder="https://example.com/pothole.jpg"
          placeholderTextColor="#64748b"
          value={photoUrl}
          onChangeText={setPhotoUrl}
        />

        <Button title="Submit Report to PMC" onPress={handleSubmit} loading={loading} />
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f172a',
  },
  content: {
    padding: 16,
  },
  card: {
    padding: 20,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#f8fafc',
    marginBottom: 16,
  },
  label: {
    color: '#cbd5e1',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 6,
    marginTop: 10,
  },
  input: {
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 10,
    padding: 12,
    color: '#f8fafc',
    fontSize: 15,
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  chipRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  chip: {
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#334155',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
  },
  chipActive: {
    backgroundColor: '#2563eb',
    borderColor: '#3b82f6',
  },
  chipText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '700',
  },
  chipTextActive: {
    color: '#ffffff',
  },
});
