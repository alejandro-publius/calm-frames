import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import BackButton from '../../components/BackButton';
import { CALM_COLORS, CALM_TEXT } from '../../calmframes/calmStyles';
import { scaleUxToDp } from '../../utils/pixelUtils';

interface Header {
  title?: string;
  navigateBack: () => void;
}

const Header = React.memo(({ title, navigateBack }: Header) => {
  return (
    <View style={styles.header}>
      <BackButton onPress={navigateBack} hasTVPreferredFocus={false} />
      <Text numberOfLines={1} style={styles.title} testID="video-player-header">
        {title}
      </Text>
    </View>
  );
});

export default Header;

const styles = StyleSheet.create({
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    opacity: 0.8,
    width: '100%',
    paddingVertical: scaleUxToDp(10),
    paddingRight: scaleUxToDp(40),
    paddingLeft: scaleUxToDp(20),
  },
  title: {
    ...CALM_TEXT.screen,
    color: CALM_COLORS.TEXT,
    textAlign: 'right',
    width: '90%',
  },
});
