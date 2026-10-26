import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import BackButton from '../../components/BackButton';
import { CALM_COLORS, CALM_SURFACE, CALM_TEXT } from '../../calmframes/calmStyles';
import { scaleUxToDp } from '../../utils/pixelUtils';

interface Header {
  title?: string;
  navigateBack: () => void;
}

const Header = React.memo(({ title, navigateBack }: Header) => {
  return (
    <View style={styles.header}>
      <Text numberOfLines={1} style={styles.title} testID="video-player-header">
        {title}
      </Text>
      <BackButton onPress={navigateBack} hasTVPreferredFocus={false} />
    </View>
  );
});

export default Header;

const styles = StyleSheet.create({
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: scaleUxToDp(20),
    width: '100%',
    paddingTop: scaleUxToDp(54),
    paddingRight: scaleUxToDp(96),
    paddingLeft: scaleUxToDp(480),
  },
  title: {
    ...CALM_TEXT.section,
    color: CALM_COLORS.TEXT,
    textAlign: 'right',
    flexShrink: 1,
    backgroundColor: CALM_COLORS.SURFACE,
    borderRadius: scaleUxToDp(CALM_SURFACE.STATUS_RADIUS),
    paddingHorizontal: scaleUxToDp(24),
    paddingVertical: scaleUxToDp(12),
  },
});
