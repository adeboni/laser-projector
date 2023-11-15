using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Runtime.InteropServices;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Shapes;

namespace ClippingGeometryTest
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : System.Windows.Window
    {
        [DllImport("gdi32.dll", EntryPoint = "DeleteObject")]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool DeleteObject([In] IntPtr hObject);

        Bitmap bmp = new Bitmap(750, 750);

        public ImageSource ImageSourceFromBitmap(Bitmap bmp)
        {
            var handle = bmp.GetHbitmap();
            try
            {
                return Imaging.CreateBitmapSourceFromHBitmap(handle, IntPtr.Zero, System.Windows.Int32Rect.Empty, BitmapSizeOptions.FromEmptyOptions());
            }
            finally { DeleteObject(handle); }
        }

        public MainWindow()
        {
            InitializeComponent();

            List<Point> poly = new List<Point>();
            
            poly.Add(new Point(100, 100));
            poly.Add(new Point(700, 100));
            poly.Add(new Point(700, 700));
            poly.Add(new Point(100, 700));
            
            /*
            poly.Add(new Point(200, 200));
            poly.Add(new Point(500, 200));
            poly.Add(new Point(600, 600));
            poly.Add(new Point(100, 600));
            */
            SetupBitmap(poly);

            List<Point> line1 = new List<Point>();
            line1.Add(new Point(650, 100));
            line1.Add(new Point(600, 150));
            DrawLine(poly, line1, Pens.Red);

            List<Point> line2 = new List<Point>();
            line2.Add(new Point(270, 250));
            line2.Add(new Point(370, 350));
            DrawLine(poly, line2, Pens.Blue);

            List<Point> line3 = new List<Point>();
            line3.Add(new Point(200, 150));
            line3.Add(new Point(500, 300));
            DrawLine(poly, line3, Pens.Green);

            List<Point> line4 = new List<Point>();
            line4.Add(new Point(50, 50));
            line4.Add(new Point(650, 650));
            DrawLine(poly, line4, Pens.Orange);

            List<Point> line5 = new List<Point>();
            line5.Add(new Point(0, 750));
            line5.Add(new Point(750, 0));
            DrawLine(poly, line5, Pens.Purple);

            MainImage.Source = ImageSourceFromBitmap(bmp);
        }

        public void SetupBitmap(List<Point> poly)
        {
            using Graphics g = Graphics.FromImage(bmp);
            g.FillRectangle(System.Drawing.Brushes.White, 0, 0, 750, 750);
            g.DrawPolygon(Pens.Black, poly.ToArray());
        }

        public void DrawLine(List<Point> poly, List<Point> line, System.Drawing.Pen pen)
        {
            using Graphics g = Graphics.FromImage(bmp);

            Point startVector = new(line[0].X, line[0].Y);
            Point endVector = new(line[1].X, line[1].Y);

            bool result = CyrusBeck.LineClipping(poly, ref startVector, ref endVector);
            //if (result)
                g.DrawLine(pen, startVector, endVector);
        }
    }

    public class CyrusBeck
    {
        public static bool LineClipping(List<Point> poly1, ref Point startVector, ref Point endVector)
        {
            int dotx = endVector.X - startVector.X;
            int doty = endVector.Y - startVector.Y;
            float tEnteringMax = 0;
            float tLeavingMin = 1;
            List<int> poly = new();
            foreach (var p in poly1)
            {
                poly.Add(p.X);
                poly.Add(p.Y);
            }

            for (int i = 0; i < 4; i++)
            {
                int normalx = poly[i*2+1] - poly[((i + 1) % 4)*2+1];
                int normaly = poly[((i + 1) % 4)*2] - poly[i*2];
                int numerator = normalx * (poly[i*2] - startVector.X) + normaly * (poly[i*2+1] - startVector.Y);
                float denominator = normalx * dotx + normaly * doty;
                float t = denominator == 0 ? numerator : numerator / denominator;

                if (denominator >= 0) tEnteringMax = Math.Max(t, tEnteringMax);
                else tLeavingMin = Math.Min(t, tLeavingMin);
            }

            if (tEnteringMax > tLeavingMin)
            {
                return false;
            }
            else
            {
                endVector = new Point((int)(startVector.X + dotx * tLeavingMin), (int)(startVector.Y + doty * tLeavingMin));
                startVector = new Point((int)(startVector.X + dotx * tEnteringMax), (int)(startVector.Y + doty * tEnteringMax));
                return true;
            }
        }
    }
}
