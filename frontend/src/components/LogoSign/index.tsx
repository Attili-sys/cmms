import { Box, Typography, useTheme } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

interface OwnProps {
  white?: boolean;
}

function Logo({ white }: OwnProps) {
  const theme = useTheme();

  return (
    <Box
      component={RouterLink}
      to="/app/work-orders"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        textDecoration: 'none',
        px: 1.5,
        py: 0.75
      }}
    >
      <Typography
        variant="subtitle2"
        sx={{
          fontWeight: 700,
          letterSpacing: '0.03em',
          color: white
            ? theme.colors.alpha.trueWhite[100]
            : theme.palette.text.primary
        }}
      >
        Powered by Canvas
      </Typography>
    </Box>
  );
}

export default Logo;
