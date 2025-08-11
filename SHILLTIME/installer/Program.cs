using System;
using System.IO;
using System.Linq;

class AssembleExe
{
    static int Main(string[] args)
    {
        try
        {
            if (args.Length != 2)
            {
                Console.WriteLine("Usage: AssembleExe <source_dir> <output_file>");
                return 1;
            }

            string sourceDir = args[0];
            string outputFile = args[1];

            // Find all part files
            var partFiles = Directory.GetFiles(sourceDir, "ProxyAssessmentTool.exe.part*")
                                    .OrderBy(f => f)
                                    .ToArray();

            if (partFiles.Length == 0)
            {
                Console.WriteLine("No part files found in " + sourceDir);
                return 1;
            }

            Console.WriteLine($"Assembling {partFiles.Length} parts into {outputFile}");

            // Delete existing file if it exists
            if (File.Exists(outputFile))
                File.Delete(outputFile);

            // Combine all parts
            using (var output = File.OpenWrite(outputFile))
            {
                foreach (var partFile in partFiles)
                {
                    using (var input = File.OpenRead(partFile))
                    {
                        input.CopyTo(output);
                    }
                }
            }

            Console.WriteLine("Assembly complete!");
            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine("Error: " + ex.Message);
            return 1;
        }
    }
}