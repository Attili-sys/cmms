import { Box, Typography } from '@mui/material';
import { Link } from 'react-router-dom';

function Logo() {
  return (
    <Box
      component={Link}
      to="/app/work-orders"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        textDecoration: 'none',
        color: 'text.primary',
        fontWeight: 700
      }}
    >
      <Typography variant="subtitle2" fontWeight={700}>
        Powered by Canvas
      </Typography>
    </Box>
  );
}

export default Logo;
