using System.Windows;
using ProxyAssessmentTool.Updater.ViewModels;

namespace ProxyAssessmentTool.Updater.Views
{
    public partial class MainWindow : Window
    {
        public MainWindow(string packagePath)
        {
            InitializeComponent();
            DataContext = new UpdateViewModel(packagePath);
        }
    }
}