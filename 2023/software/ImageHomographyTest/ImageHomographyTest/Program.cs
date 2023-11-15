#pragma warning disable CA1416

using System.Drawing;

Bitmap sourceImage = new(1000, 1000);
Graphics g = Graphics.FromImage(sourceImage);
g.FillRectangle(Brushes.Black, 0, 0, 1000, 1000);
g.FillRectangle(Brushes.Blue, 250, 250, 500, 500);
sourceImage.Save("input.png");

List<PointF> srcPts = new() { new PointF(250, 250), new PointF(750, 250), new PointF(250, 750), new PointF(750, 750) };
//List<PointF> dstPts = new() { new PointF(250, 250), new PointF(750, 250), new PointF(250, 750), new PointF(750, 750) };
List<PointF> dstPts = new() { new PointF(250 - 150, 250 - 100), new PointF(750 - 100, 250 - 100), new PointF(250 - 100, 750 + 100), new PointF(750 + 100, 750 + 100) };

float[] homography = FindHomography(srcPts, dstPts);
//float[] homography = { 1, 0, 0, 0, 1, 0, 0, 0, 1};
Bitmap outputImage = WarpPerspective(sourceImage, homography, new Size(1000, 1000));
outputImage.Save("output.png");

static Bitmap WarpPerspective(Bitmap src, float[] homography, Size size)
{
    Bitmap dst = new(size.Width, size.Height);

    for (int i = 0; i < src.Width; i++)
    {
        for (int j = 0; j < src.Height; j++)
        {
            var dst1 = homography[0] * i + homography[1] * j + homography[2];
            var dst2 = homography[3] * i + homography[4] * j + homography[5];
            var dst3 = homography[6] * i + homography[7] * j + homography[8];

            int x = (int)(dst1 / dst3);
            int y = (int)(dst2 / dst3);

            if (x >= 0 && x < size.Width && y >= 0 && y < size.Height)
                dst.SetPixel(x, y, src.GetPixel(i, j));
        }
    }

    return dst;
}

static float[] FindHomography(List<PointF> srcPoints, List<PointF> dstPoints)
{
    float[][] coefficientMatrix = MatrixCreate(8, 8);

    for (int i = 0; i < 4; i++)
    {
        coefficientMatrix[2 * i][0] = srcPoints[i].X;
        coefficientMatrix[2 * i][1] = srcPoints[i].Y;
        coefficientMatrix[2 * i][2] = 1;
        coefficientMatrix[2 * i][3] = 0;
        coefficientMatrix[2 * i][4] = 0;
        coefficientMatrix[2 * i][5] = 0;
        coefficientMatrix[2 * i][6] = -dstPoints[i].X * srcPoints[i].X;
        coefficientMatrix[2 * i][7] = -dstPoints[i].X * srcPoints[i].Y;

        coefficientMatrix[2 * i + 1][0] = 0;
        coefficientMatrix[2 * i + 1][1] = 0;
        coefficientMatrix[2 * i + 1][2] = 0;
        coefficientMatrix[2 * i + 1][3] = srcPoints[i].X;
        coefficientMatrix[2 * i + 1][4] = srcPoints[i].Y;
        coefficientMatrix[2 * i + 1][5] = 1;
        coefficientMatrix[2 * i + 1][6] = -dstPoints[i].Y * srcPoints[i].X;
        coefficientMatrix[2 * i + 1][7] = -dstPoints[i].Y * srcPoints[i].Y;
    }

    float[][] inverseCoefficientMatrix = MatrixInverse(coefficientMatrix);

    float[] dstVec = new float[8];
    for (int i = 0; i < 4; i++)
    {
        dstVec[i * 2] = dstPoints[i].X;
        dstVec[i * 2 + 1] = dstPoints[i].Y;
    }
   
    float[] res = new float[9];
    for (int i = 0; i < 8; i++)
    {
        res[i] = 0;
        for (int k = 0; k < 8; k++)
            res[i] += inverseCoefficientMatrix[i][k] * dstVec[k];
    }
    res[8] = 1;

    return res;
}


static float[][] MatrixCreate(int rows, int cols)
{
    float[][] result = new float[rows][];
    for (int i = 0; i < rows; ++i)
        result[i] = new float[cols];
    return result;
}

static float[][] MatrixInverse(float[][] matrix)
{
    float[][] result = MatrixDuplicate(matrix);
    float[][] lum = MatrixDecompose(matrix, out int[] perm);

    float[] x = new float[8];
    for (int i = 0; i < 8; ++i)
    {
        for (int j = 0; j < 8; ++j)
            x[j] = i == perm[j] ? 1.0f : 0.0f;

        for (int k = 1; k < 8; ++k)
        {
            float sum = x[k];
            for (int w = 0; w < k; ++w)
                sum -= lum[k][w] * x[w];
            x[k] = sum;
        }

        x[7] /= lum[7][7];
        for (int k = 6; k >= 0; --k)
        {
            float sum = x[k];
            for (int w = k + 1; w < 8; ++w)
                sum -= lum[k][w] * x[w];
            x[k] = sum / lum[k][k];
        }

        for (int j = 0; j < 8; ++j)
            result[j][i] = x[j];
    }
    return result;
}

static float[][] MatrixDuplicate(float[][] matrix)
{
    float[][] result = MatrixCreate(8, 8);
    for (int i = 0; i < 8; ++i)
        for (int j = 0; j < 8; ++j)
            result[i][j] = matrix[i][j];
    return result;
}


static float[][] MatrixDecompose(float[][] matrix, out int[] perm)
{
    float[][] result = MatrixDuplicate(matrix);

    perm = new int[8];
    for (int i = 0; i < 8; ++i)
        perm[i] = i;

    for (int j = 0; j < 7; ++j)
    {
        float colMax = Math.Abs(result[j][j]);
        int pRow = j;

        for (int i = j + 1; i < 8; ++i)
        {
            if (Math.Abs(result[i][j]) > colMax)
            {
                colMax = Math.Abs(result[i][j]);
                pRow = i;
            }
        }

        if (pRow != j)
        {
            (result[j], result[pRow]) = (result[pRow], result[j]);
            (perm[j], perm[pRow]) = (perm[pRow], perm[j]);
        }


        if (result[j][j] == 0.0)
        {
            int goodRow = -1;
            for (int row = j + 1; row < 8; ++row)
                if (result[row][j] != 0.0)
                    goodRow = row;

            if (goodRow == -1)
                return result;

            (result[j], result[goodRow]) = (result[goodRow], result[j]);
            (perm[j], perm[goodRow]) = (perm[goodRow], perm[j]);
        }

        for (int i = j + 1; i < 8; ++i)
        {
            result[i][j] /= result[j][j];
            for (int k = j + 1; k < 8; ++k)
                result[i][k] -= result[i][j] * result[j][k];
        }
    }

    return result;
}