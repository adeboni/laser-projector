using Emgu.CV;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ImageHomographyTestFW
{
    internal class Program
    {
        static void Main(string[] args)
        {
            Bitmap bmp = new Bitmap(1000, 1000, System.Drawing.Imaging.PixelFormat.Format32bppPArgb);
            Graphics g = Graphics.FromImage(bmp);
            g.FillRectangle(Brushes.White, 0, 0, 1000, 1000);
            g.FillRectangle(Brushes.Blue, 250, 250, 500, 500);
            bmp.Save("input.png");
            /*
            List<PointF> srcPts = new()
            {
                new PointF(250, 250),
                new PointF(750, 250),
                new PointF(250, 750),
                new PointF(750, 750)
            };

            List<PointF> dstPts = new()
            {
                new PointF(250 + 100, 250 - 100),
                new PointF(750 - 100, 250 - 100),
                new PointF(250 - 100, 750 + 100),
                new PointF(750 + 100, 750 + 100)
            };
            */
            List<PointF> srcPts = new List<PointF>()
{
    new PointF(141, 131),
    new PointF(480, 159),
    new PointF(493, 630),
    new PointF(64, 601)
};

            List<PointF> dstPts = new List<PointF>()
{
    new PointF(318, 256),
    new PointF(534, 372),
    new PointF(316, 670),
    new PointF(73, 473)
};

            Mat cvHomography = CvInvoke.FindHomography(srcPts.ToArray(), dstPts.ToArray());
            Mat outputImage = new Mat();
            CvInvoke.WarpPerspective(bmp.ToMat(), outputImage, cvHomography, new Size(1000, 1000));
            outputImage.ToBitmap().Save("outputCV.png");


        }
    }
}
