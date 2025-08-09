import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { User, UserPreferences } from '../types';

const mockUser: User = {
  id: '1',
  name: 'John Doe',
  email: 'john.doe@example.com',
  interests: ['Technology', 'Politics', 'Finance', 'World Events'],
  languageStyle: 'Professional',
  preferences: {
    darkMode: false,
    notifications: true,
    languageStyle: 'Professional',
    interests: ['Technology', 'Politics', 'Finance', 'World Events'],
  },
};

const languageStyles = [
  { id: 'genz', name: 'Gen Z', description: 'Casual and trendy language' },
  { id: 'professional', name: 'Professional', description: 'Formal and business-like' },
  { id: 'informative', name: 'Informative', description: 'Clear and educational' },
  { id: 'friendly', name: 'Friendly', description: 'Warm and approachable' },
];

const interests = [
  'Politics', 'Technology', 'Sports', 'Finance', 
  'World Events', 'Health', 'Science', 'Entertainment'
];

const ProfileScreen: React.FC = ({ navigation }: any) => {
  const [user, setUser] = useState<User>(mockUser);
  const [selectedLanguageStyle, setSelectedLanguageStyle] = useState(user.preferences.languageStyle);

  const handleLanguageStyleChange = (style: 'Professional' | 'Gen Z' | 'Informative' | 'Friendly') => {
    setSelectedLanguageStyle(style);
    setUser(prev => ({
      ...prev,
      preferences: { ...prev.preferences, languageStyle: style },
    }));
  };

  const handleInterestToggle = (interest: string) => {
    const newInterests = user.interests.includes(interest)
      ? user.interests.filter(i => i !== interest)
      : [...user.interests, interest];
    
    setUser(prev => ({
      ...prev,
      interests: newInterests,
      preferences: { ...prev.preferences, interests: newInterests },
    }));
  };

  const handlePreferenceToggle = (key: keyof UserPreferences, value: boolean) => {
    setUser(prev => ({
      ...prev,
      preferences: { ...prev.preferences, [key]: value },
    }));
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatarContainer}>
            <View style={styles.avatar}>
              <Ionicons name="person" size={32} color="#64748b" />
            </View>
          </View>
          <Text style={styles.userName}>{user.name}</Text>
          <Text style={styles.userEmail}>{user.email}</Text>
        </View>

        {/* Language Style Preferences */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Language Style</Text>
          <Text style={styles.sectionSubtitle}>How would you like your news written?</Text>
          
          {languageStyles.map(style => (
            <TouchableOpacity
              key={style.id}
              style={[
                styles.languageOption,
                selectedLanguageStyle === style.name && styles.languageOptionActive
              ]}
                             onPress={() => handleLanguageStyleChange(style.name as 'Professional' | 'Gen Z' | 'Informative' | 'Friendly')}
            >
              <View style={styles.languageOptionContent}>
                <Text style={[
                  styles.languageOptionTitle,
                  selectedLanguageStyle === style.name && styles.languageOptionTitleActive
                ]}>
                  {style.name}
                </Text>
                <Text style={[
                  styles.languageOptionDescription,
                  selectedLanguageStyle === style.name && styles.languageOptionDescriptionActive
                ]}>
                  {style.description}
                </Text>
              </View>
              {selectedLanguageStyle === style.name && (
                <Ionicons name="checkmark-circle" size={24} color="#2563eb" />
              )}
            </TouchableOpacity>
          ))}
        </View>

        {/* Interests */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Interests</Text>
          <Text style={styles.sectionSubtitle}>Select topics you're interested in</Text>
          
          <View style={styles.interestsGrid}>
            {interests.map(interest => (
              <TouchableOpacity
                key={interest}
                style={[
                  styles.interestChip,
                  user.interests.includes(interest) && styles.interestChipActive
                ]}
                onPress={() => handleInterestToggle(interest)}
              >
                <Text style={[
                  styles.interestText,
                  user.interests.includes(interest) && styles.interestTextActive
                ]}>
                  {interest}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* App Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>App Settings</Text>
          
          <View style={styles.settingItem}>
            <View style={styles.settingContent}>
              <Ionicons name="moon-outline" size={24} color="#64748b" />
              <View style={styles.settingText}>
                <Text style={styles.settingTitle}>Dark Mode</Text>
                <Text style={styles.settingDescription}>Switch to dark theme</Text>
              </View>
            </View>
            <Switch
              value={user.preferences.darkMode}
              onValueChange={(value) => handlePreferenceToggle('darkMode', value)}
              trackColor={{ false: '#e2e8f0', true: '#2563eb' }}
              thumbColor="#ffffff"
            />
          </View>
          
          <View style={styles.settingItem}>
            <View style={styles.settingContent}>
              <Ionicons name="notifications-outline" size={24} color="#64748b" />
              <View style={styles.settingText}>
                <Text style={styles.settingTitle}>Notifications</Text>
                <Text style={styles.settingDescription}>Get notified about new stories</Text>
              </View>
            </View>
            <Switch
              value={user.preferences.notifications}
              onValueChange={(value) => handlePreferenceToggle('notifications', value)}
              trackColor={{ false: '#e2e8f0', true: '#2563eb' }}
              thumbColor="#ffffff"
            />
          </View>
        </View>

        {/* About Civora AI */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About Civora AI</Text>
          
          <View style={styles.aboutCard}>
            <View style={styles.aboutHeader}>
              <Ionicons name="shield-checkmark-outline" size={24} color="#10b981" />
              <Text style={styles.aboutTitle}>Our Mission</Text>
            </View>
            <Text style={styles.aboutText}>
              We believe in presenting news as it is, without political bias or distortion. 
              Our AI technology analyzes multiple sources to deliver balanced, unbiased reporting.
            </Text>
          </View>
          
          <View style={styles.aboutCard}>
            <View style={styles.aboutHeader}>
              <Ionicons name="analytics-outline" size={24} color="#2563eb" />
              <Text style={styles.aboutTitle}>Bias Detection</Text>
            </View>
            <Text style={styles.aboutText}>
              Our advanced NLP algorithms quantify ideological bias and synthesize 
              balanced content from diverse perspectives.
            </Text>
          </View>
        </View>

        {/* App Info */}
        <View style={styles.section}>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>App Version</Text>
            <Text style={styles.infoValue}>1.0.0</Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>Last Updated</Text>
            <Text style={styles.infoValue}>January 15, 2024</Text>
          </View>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  content: {
    flex: 1,
  },
  profileHeader: {
    alignItems: 'center',
    paddingVertical: 30,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  avatarContainer: {
    marginBottom: 16,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#f1f5f9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  userName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 14,
    color: '#64748b',
  },
  section: {
    backgroundColor: '#ffffff',
    marginTop: 16,
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 16,
  },
  languageOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    marginBottom: 12,
    backgroundColor: '#ffffff',
  },
  languageOptionActive: {
    borderColor: '#2563eb',
    backgroundColor: '#eff6ff',
  },
  languageOptionContent: {
    flex: 1,
  },
  languageOptionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 4,
  },
  languageOptionTitleActive: {
    color: '#2563eb',
  },
  languageOptionDescription: {
    fontSize: 14,
    color: '#64748b',
  },
  languageOptionDescriptionActive: {
    color: '#3b82f6',
  },
  interestsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  interestChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    backgroundColor: '#ffffff',
  },
  interestChipActive: {
    backgroundColor: '#2563eb',
    borderColor: '#2563eb',
  },
  interestText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#64748b',
  },
  interestTextActive: {
    color: '#ffffff',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  settingContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingText: {
    marginLeft: 12,
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 2,
  },
  settingDescription: {
    fontSize: 14,
    color: '#64748b',
  },
  aboutCard: {
    backgroundColor: '#f8fafc',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  aboutHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  aboutTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginLeft: 8,
  },
  aboutText: {
    fontSize: 14,
    color: '#64748b',
    lineHeight: 20,
  },
  infoItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  infoLabel: {
    fontSize: 14,
    color: '#64748b',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1e293b',
  },
});

export default ProfileScreen; 