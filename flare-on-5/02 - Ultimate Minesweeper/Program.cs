using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;

namespace flare_02
{
    class Program
    {
        private static string GetKey(List<uint> revealedCells)
        {
            revealedCells.Sort();
            Random random = new Random(Convert.ToInt32(revealedCells[0] << 20 | revealedCells[1] << 10 | revealedCells[2]));
            byte[] array = new byte[32];
            byte[] array2 = new byte[]
            {
                245,
                75,
                65,
                142,
                68,
                71,
                100,
                185,
                74,
                127,
                62,
                130,
                231,
                129,
                254,
                243,
                28,
                58,
                103,
                179,
                60,
                91,
                195,
                215,
                102,
                145,
                154,
                27,
                57,
                231,
                241,
                86
            };
            random.NextBytes(array);
            uint num = 0u;
            while ((ulong)num < (ulong)((long)array2.Length))
            {
                array2[num] = (byte) (array2[num] ^ array[num]);
                num += 1u;
            }
            return Encoding.ASCII.GetString(array2);
        }
        static void Main(string[] args)
        {
            List<uint> decoded = VALLOC_TYPES.Select((x) =>
            {
                uint u = ~x;
                uint r = u / 30u;
                uint c = u - r * 30u;
                return (r - 1) * 30u + c - 1;
            }).ToList();
            Debug.WriteLine(GetKey(decoded));
        }
        private static uint VALLOC_TYPE_HEADER_PAGE = 4294966400u;

        // Token: 0x04000008 RID: 8
        private static uint VALLOC_TYPE_HEADER_POOL = 4294966657u;

        // Token: 0x04000009 RID: 9
        private static uint VALLOC_TYPE_HEADER_RESERVED = 4294967026u;

        // Token: 0x0400000A RID: 10
        private static uint[] VALLOC_TYPES = new uint[]
        {
            VALLOC_TYPE_HEADER_PAGE,
            VALLOC_TYPE_HEADER_POOL,
            VALLOC_TYPE_HEADER_RESERVED
        };
    }
}
