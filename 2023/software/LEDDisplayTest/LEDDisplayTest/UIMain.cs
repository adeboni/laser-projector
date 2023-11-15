using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Configuration;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Net.Sockets;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Threading;

namespace LEDDisplayTest
{
    public partial class UIMain : Form
    {
        private readonly int innerDiameter = 22000;
        private readonly int outerDiameter = 95000;
        private readonly int innerLedRadius;
        private readonly int imageWidth;
        private readonly int spokes = 64;
        private readonly int ledsPerSpoke = 400;
        private readonly int port = 8080;
        private readonly string address = "127.0.0.1";

        public UIMain()
        {
            InitializeComponent();

            innerDiameter = int.Parse(ConfigurationManager.AppSettings["InnerDiameter"]);
            outerDiameter = int.Parse(ConfigurationManager.AppSettings["OuterDiameter"]);
            spokes = int.Parse(ConfigurationManager.AppSettings["LedSpokes"]);
            ledsPerSpoke = int.Parse(ConfigurationManager.AppSettings["LedsPerSpoke"]);
            port = int.Parse(ConfigurationManager.AppSettings["Port"]);
            address = ConfigurationManager.AppSettings["Host"];

            innerLedRadius = (int)(innerDiameter * ledsPerSpoke / ((outerDiameter - innerDiameter) / 2.0) / 2);
            imageWidth = innerLedRadius * 2 + ledsPerSpoke * 2 + 20;

            this.FormClosing += UIMain_FormClosing;
        }

        private void UIMain_FormClosing(object sender, FormClosingEventArgs e)
        {
            Environment.Exit(0);
        }

        private void Pol2Cart(double rho, double phi, out int x, out int y)
        {
            x = (int)(rho * Math.Cos(phi)) + imageWidth / 2;
            y = (int)(rho * Math.Sin(phi)) + imageWidth / 2;
        }

        private Bitmap DrawImage(byte[] ledValues)
        {
            Bitmap bmp = new Bitmap(imageWidth, imageWidth, System.Drawing.Imaging.PixelFormat.Format24bppRgb);

            Rectangle rect = new Rectangle(0, 0, bmp.Width, bmp.Height);
            System.Drawing.Imaging.BitmapData bmpData =
                bmp.LockBits(rect, System.Drawing.Imaging.ImageLockMode.ReadWrite, bmp.PixelFormat);

            // Get the address of the first line.
            IntPtr ptr = bmpData.Scan0;

            // Declare an array to hold the bytes of the bitmap.
            int bytes = Math.Abs(bmpData.Stride) * bmp.Height;
            byte[] rgbValues = new byte[bytes];

            // Copy the RGB values into the array.
            System.Runtime.InteropServices.Marshal.Copy(ptr, rgbValues, 0, bytes);

            for (int i = 0; i < spokes * ledsPerSpoke * 3; i++)
            {
                int c = i % 3;
                int t = (i / 3) % spokes;
                int r = i / (3 * spokes);

                Pol2Cart(r + innerLedRadius, t * 6.28 / spokes, out int x, out int y);
                int certainPixel = ((y * imageWidth) + x) * 3;
                rgbValues[certainPixel + c] = ledValues[i];
            }

            // Copy the RGB values back to the bitmap
            System.Runtime.InteropServices.Marshal.Copy(rgbValues, 0, ptr, bytes);

            // Unlock the bits.
            bmp.UnlockBits(bmpData);
            return bmp;
        }

        private void StartServer()
        {
            while (true)
            {
                IPAddress ipAddr = IPAddress.Parse(address);
                IPEndPoint localEndPoint = new IPEndPoint(ipAddr, port);
                Socket listener = new Socket(ipAddr.AddressFamily, SocketType.Stream, ProtocolType.Tcp);

                try
                {
                    listener.Bind(localEndPoint);
                    listener.Listen(10);

                    while (true)
                    {
                        Socket clientSocket = listener.Accept();

                        byte[] bytes = new byte[ledsPerSpoke * spokes * 3];

                        while (clientSocket.Available > 0)
                            clientSocket.Receive(bytes);

                        clientSocket.Shutdown(SocketShutdown.Both);
                        clientSocket.Close();

                        Bitmap bmp = DrawImage(bytes);
                        this.Invoke((MethodInvoker)delegate {
                            pictureBox.Image = bmp;
                        });
                    }
                }
                catch (Exception e)
                {
                    Console.WriteLine(e.ToString());
                }
            }
        }

        private void UIMain_Load(object sender, EventArgs e)
        {
            new Thread(StartServer).Start();
        }
    }
}
