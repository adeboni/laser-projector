using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using System.Windows.Interop;
using System.Windows.Media.Imaging;

namespace FontEditor
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : System.Windows.Window
    {
        [DllImport("gdi32.dll", EntryPoint = "DeleteObject")]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool DeleteObject([In] IntPtr hObject);

        private readonly Bitmap bmp = new(1200, 1200);
        private readonly Pen pen = new(Brushes.Blue, 10);
        private readonly List<FontObject> fonts = new();
        private readonly List<Point> userPoints = new();
        private readonly List<bool> userOns = new();
        private bool lastClick = false;

        public static System.Windows.Media.ImageSource ImageSourceFromBitmap(Bitmap bmp)
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

            LoadFonts();

            string buffer = "";
            foreach (var file in Directory.GetFiles("vectors"))
            {
                var range = GetLMCodeRange(file);
                float xAdj = (range.Item2 - range.Item1) / 2;
                float yAdj = (range.Item4 - range.Item3) / 2;
                buffer += ConvertLMCode(file, GetLMCodeScale(file, range.Item1, range.Item3), range.Item1, range.Item3) + "\r\n";
            }
            File.WriteAllText("vectorData.txt", buffer);
            
            
            float catXmin = float.MaxValue;
            float catXmax = float.MinValue;
            float catYmin = float.MaxValue;
            float catYmax = float.MinValue;

            foreach (var file in Directory.GetFiles("cat"))
            {
                var range = GetLMCodeRange(file);
                catXmin = Math.Min(catXmin, range.Item1);
                catXmax = Math.Max(catXmax, range.Item2);
                catYmin = Math.Min(catYmin, range.Item3);
                catYmax = Math.Max(catYmax, range.Item4);
            }

            float catXadj = (catXmax - catXmin) / 2;
            float catYadj = (catYmax - catYmin) / 2;

            float catScale = float.MaxValue;
            foreach (var file in Directory.GetFiles("cat"))
                catScale = Math.Min(catScale, GetLMCodeScale(file, catXmin, catYmin));

            string catBuffer = "";
            foreach (var file in Directory.GetFiles("cat"))
                catBuffer += ConvertLMCode(file, catScale, catXmin, catYmin) + "\r\n";
            File.WriteAllText("catData.txt", catBuffer);



            float toasterXmin = float.MaxValue;
            float toasterXmax = float.MinValue;
            float toasterYmin = float.MaxValue;
            float toasterYmax = float.MinValue;

            foreach (var file in Directory.GetFiles("toaster"))
            {
                var range = GetLMCodeRange(file);
                toasterXmin = Math.Min(toasterXmin, range.Item1);
                toasterXmax = Math.Max(toasterXmax, range.Item2);
                toasterYmin = Math.Min(toasterYmin, range.Item3);
                toasterYmax = Math.Max(toasterYmax, range.Item4);
            }

            float toasterXadj = (toasterXmax - toasterXmin) / 2;
            float toasterYadj = (toasterYmax - toasterYmin) / 2;

            float toasterScale = float.MaxValue;
            foreach (var file in Directory.GetFiles("toaster"))
                toasterScale = Math.Min(toasterScale, GetLMCodeScale(file, toasterXmin, toasterYmin));

            string toasterBuffer = "";
            foreach (var file in Directory.GetFiles("toaster"))
                toasterBuffer += ConvertLMCode(file, toasterScale, toasterXmin, toasterYmin) + "\r\n";
            File.WriteAllText("toasterData.txt", toasterBuffer);
        }

        public void ClearImage()
        {
            using Graphics g = Graphics.FromImage(bmp);
            g.FillRectangle(Brushes.White, 0, 0, bmp.Width, bmp.Height);
            MainImage.Source = ImageSourceFromBitmap(bmp);
        }

        public void LoadFonts()
        {
            foreach (Match match in Regex.Matches(File.ReadAllText("Font.h"), @"(const [^;]+;)"))
            {
                Match name = Regex.Match(match.Groups[1].Value, @"short (.*)\[\]");

                List<string> points = new();
                foreach (Match m in Regex.Matches(match.Groups[1].Value, "(0x[^,]*),"))
                    points.Add(m.Groups[1].Value);

                FontObject fo = new(name.Groups[1].Value, points);
                fonts.Add(fo);
                CboFont.Items.Add(fo.Name);
            }
        }

        public void DrawCharacter(FontObject fo)
        {
            Point min = new Point(int.MaxValue, int.MaxValue);
            Point max = new Point(int.MinValue, int.MinValue);

            using Graphics g = Graphics.FromImage(bmp);
            g.FillRectangle(Brushes.White, 0, 0, bmp.Width, bmp.Height);
            for (int i = 1; i < fo.Points.Count; i++)
            {
                max = new Point(Math.Max(max.X, fo.Points[i].X), Math.Max(max.Y, fo.Points[i].Y));
                min = new Point(Math.Min(min.X, fo.Points[i].X), Math.Min(min.Y, fo.Points[i].Y));
                if (fo.Points[i].On)
                    g.DrawLine(pen, fo.Points[i].ToPoint(), fo.Points[i - 1].ToPoint());
            }
            MainImage.Source = ImageSourceFromBitmap(bmp);
            TxtInfo.Text = $"Min: {min}    Max: {max}";
        }

        public void DrawUserFont()
        {
            Point min = new Point(int.MaxValue, int.MaxValue);
            Point max = new Point(int.MinValue, int.MinValue);

            using Graphics g = Graphics.FromImage(bmp);
            g.FillRectangle(Brushes.White, 0, 0, bmp.Width, bmp.Height);
            for (int i = 1; i < userPoints.Count; i++)
            {
                max = new Point(Math.Max(max.X, userPoints[i].X), Math.Max(max.Y, userPoints[i].Y));
                min = new Point(Math.Min(min.X, userPoints[i].X), Math.Min(min.Y, userPoints[i].Y));
                if (userOns[i])
                    g.DrawLine(pen, userPoints[i], userPoints[i - 1]);
            }
            MainImage.Source = ImageSourceFromBitmap(bmp);
            TxtInfo.Text = $"Min: {min}    Max: {max}";
        }

        private void CboFont_SelectionChanged(object sender, System.Windows.Controls.SelectionChangedEventArgs e)
        {
            if (CboFont.SelectedIndex < 0) return;
            DrawCharacter(fonts[CboFont.SelectedIndex]);
        }


        private void ImageMouseDown(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            return;

            System.Windows.Point p = e.GetPosition(MainImage);
            double pixelWidth = MainImage.Source.Width;
            double pixelHeight = MainImage.Source.Height;
            double x = pixelWidth * p.X / MainImage.ActualWidth;
            double y = pixelHeight * p.Y / MainImage.ActualHeight;
            Point newPoint = new Point((int)x, (int)y);

            if (e.LeftButton == System.Windows.Input.MouseButtonState.Pressed)
            {
                userPoints.Add(newPoint);
                userOns.Add(lastClick);
                lastClick = true;
            }
            else if (e.RightButton == System.Windows.Input.MouseButtonState.Pressed)
            {
                lastClick = false;
            }

            DrawUserFont();
        }

        private double GetXCenter(IEnumerable<Point> points)
        {
            double sum = 0;
            foreach (var p in points)
                sum += p.X;
            return sum / points.Count();
        }

        private void ReorderVectors()
        {
            List<(List<Point>, List<bool>)> lineSegs = new();

            int startIndex = 0;
            for (int i = 0; i < userPoints.Count + 1; i++)
            {
                if (i == userPoints.Count || userOns[i] == false)
                {
                    if (startIndex != i)
                    {
                        lineSegs.Add((userPoints.GetRange(startIndex, i - startIndex), userOns.GetRange(startIndex, i - startIndex)));
                        startIndex = i;
                    }
                }
            }

    
            lineSegs = lineSegs.OrderBy(x => GetXCenter(x.Item1)).ToList();
            userOns.Clear();
            userPoints.Clear();

            foreach (var seg in lineSegs)
            {
                userPoints.AddRange(seg.Item1);
                userOns.AddRange(seg.Item2);
            }
        }

        private (float, float, float, float) GetLMCodeRange(string path)
        {
            float xMin = float.MaxValue;
            float xMax = float.MinValue;
            float yMin = float.MaxValue;
            float yMax = float.MinValue;

            foreach (string line in File.ReadLines(path))
            {
                if (line.Trim().Length == 0) continue;
                var splitLine = line.Split(' ').Select(s => s.Trim()).ToArray();
                float x = float.Parse(splitLine[1]) + 10000;
                float y = float.Parse(splitLine[2]) + 10000;

                xMin = Math.Min(xMin, x);
                xMax = Math.Max(xMax, x);
                yMin = Math.Min(yMin, y);
                yMax = Math.Max(yMax, y);
            }

            return (xMin, xMax, yMin, yMax);
        }

        private float GetLMCodeScale(string path, float xAdj, float yAdj)
        {
            float scale = float.MaxValue;
            foreach (string line in File.ReadLines(path))
            {
                if (line.Trim().Length == 0) continue;
                var splitLine = line.Split(' ').Select(s => s.Trim()).ToArray();
                float x = float.Parse(splitLine[1]) + 10000 - xAdj;
                float y = float.Parse(splitLine[2]) + 10000 - yAdj;
                scale = Math.Min(scale, 1100 / x);
                scale = Math.Min(scale, 1100 / y);
            }

            return scale;
        }

        private string ConvertLMCode(string path, float scale, float xAdj, float yAdj)
        {
            userOns.Clear();
            userPoints.Clear();

            List<PointF> tempPoints = new();
            foreach (string line in File.ReadLines(path))
            {
                if (line.Trim().Length == 0) continue;
                var splitLine = line.Split(' ').Select(s => s.Trim()).ToArray();
                userOns.Add(splitLine[0] == "L");
                float x = float.Parse(splitLine[1]) + 10000 - xAdj;
                float y = float.Parse(splitLine[2]) + 10000 - yAdj;
                tempPoints.Add(new PointF(x, y));
            }

            foreach (var p in tempPoints)
                userPoints.Add(new Point((int)(p.X * scale), (int)(p.Y * scale)));

            ReorderVectors();
            DrawUserFont();
            return GetImageText(Path.GetFileNameWithoutExtension(path).Replace("-", ""));
        }

        private string GetImageText(string name = "NAME")
        {
            string buffer = $"const unsigned short draw_{name}[] PROGMEM = {{\r\n";
            for (int i = 0; i < userPoints.Count; i++)
                buffer += $"0x{(userOns[i] ? (userPoints[i].X | 0x8000).ToString("X") : userPoints[i].X.ToString("X"))},0x{(1100 - userPoints[i].Y).ToString("X")},\r\n";
            buffer += "};";
            return buffer;
        }

        private void Save_Click(object sender, System.Windows.RoutedEventArgs e)
        {
            TextCopy.ClipboardService.SetText(GetImageText());
        }

        private void Clear_Click(object sender, System.Windows.RoutedEventArgs e)
        {
            ClearImage();
            userPoints.Clear();
            userOns.Clear();
            lastClick = false;
        }
    }

    public class FontObject
    {
        public string Name { get; }

        public List<FontPoint> Points { get; } = new List<FontPoint>();

        public FontObject(string name, List<string> points)
        {
            Name = name;

            for (int i = 0; i < points.Count; i += 2)
            {
                int x = Convert.ToInt32(points[i], 16);
                int y = Convert.ToInt32(points[i + 1], 16);

                FontPoint fp = new(x & 0x7fff, 1100 - y, (x & 0x8000) > 0);
                Points.Add(fp);
            }
        }
    }

    public class FontPoint
    {
        public int X { get; }
        public int Y { get; }
        public bool On { get; }

        public FontPoint(int x, int y, bool on)
        {
            X = x;
            Y = y;
            On = on;
        }

        public Point ToPoint()
        {
            return new Point(X + 20, Y + 20);
        }
    }
}
