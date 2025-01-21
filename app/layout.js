import './globals.css';

export const metadata = {
  title: 'Schengen Vizesi Randevu Arama',
  description: 'Modern web arayüzlü, gerçek zamanlı bildirim sistemine sahip Schengen vize randevu kontrol uygulaması.',
  icons: {
    icon: [
      {
        url: '/schengen-visa-appointment/favicon.ico',
        sizes: 'any'
      }
    ]
  }
};

export default function RootLayout({ children }) {
  return (
    <html lang="tr">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
          rel="stylesheet"
          crossOrigin="anonymous"
        />
        <link
          rel="stylesheet"
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
          crossOrigin="anonymous"
        />
      </head>
      <body>{children}</body>
    </html>
  );
} 