using System;
using System.Collections;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Data;
using System.Windows.Input;
using System.Globalization;
using System.Windows;

namespace ProxyAssessmentTool.Core.Performance
{
    /// <summary>
    /// Generic pagination interface
    /// </summary>
    public interface IPage<T>
    {
        int PageNumber { get; }
        int PageSize { get; }
        int TotalCount { get; }
        int TotalPages { get; }
        bool HasPrevious { get; }
        bool HasNext { get; }
        IReadOnlyList<T> Items { get; }
    }

    /// <summary>
    /// Paginated result implementation
    /// </summary>
    public sealed class Page<T> : IPage<T>
    {
        public int PageNumber { get; }
        public int PageSize { get; }
        public int TotalCount { get; }
        public int TotalPages { get; }
        public bool HasPrevious => PageNumber > 1;
        public bool HasNext => PageNumber < TotalPages;
        public IReadOnlyList<T> Items { get; }

        public Page(IEnumerable<T> items, int pageNumber, int pageSize, int totalCount)
        {
            Items = items?.ToList().AsReadOnly() ?? new List<T>().AsReadOnly();
            PageNumber = Math.Max(1, pageNumber);
            PageSize = Math.Max(1, pageSize);
            TotalCount = Math.Max(0, totalCount);
            TotalPages = (int)Math.Ceiling(totalCount / (double)pageSize);
        }

        public static Page<T> Empty(int pageSize = 50) => 
            new(Enumerable.Empty<T>(), 1, pageSize, 0);
    }

    /// <summary>
    /// Pagination service for managing paginated data
    /// </summary>
    public interface IPaginationService<T>
    {
        Task<IPage<T>> GetPageAsync(int pageNumber, int pageSize, CancellationToken cancellationToken = default);
        Task<IPage<T>> GetPageAsync(int pageNumber, int pageSize, Func<IQueryable<T>, IOrderedQueryable<T>> orderBy, CancellationToken cancellationToken = default);
        Task<IPage<T>> GetPageAsync(int pageNumber, int pageSize, Func<IQueryable<T>, IQueryable<T>> filter, Func<IQueryable<T>, IOrderedQueryable<T>> orderBy, CancellationToken cancellationToken = default);
    }

    /// <summary>
    /// Observable collection supporting incremental loading for WPF virtualization
    /// </summary>
    public class IncrementalLoadingCollection<T> : ObservableCollection<T>, ISupportIncrementalLoading, INotifyPropertyChanged
    {
        private readonly Func<int, int, CancellationToken, Task<IPage<T>>> _loadPageFunc;
        private readonly int _pageSize;
        private int _currentPage;
        private bool _hasMoreItems;
        private bool _isLoading;
        private int _totalCount;

        public bool HasMoreItems => _hasMoreItems;
        
        public bool IsLoading
        {
            get => _isLoading;
            private set
            {
                if (_isLoading != value)
                {
                    _isLoading = value;
                    OnPropertyChanged();
                }
            }
        }

        public int TotalCount
        {
            get => _totalCount;
            private set
            {
                if (_totalCount != value)
                {
                    _totalCount = value;
                    OnPropertyChanged();
                }
            }
        }

        public IncrementalLoadingCollection(
            Func<int, int, CancellationToken, Task<IPage<T>>> loadPageFunc,
            int pageSize = 50)
        {
            _loadPageFunc = loadPageFunc ?? throw new ArgumentNullException(nameof(loadPageFunc));
            _pageSize = Math.Max(1, pageSize);
            _currentPage = 0;
            _hasMoreItems = true;
        }

        public async Task<LoadMoreItemsResult> LoadMoreItemsAsync(uint count)
        {
            if (IsLoading || !HasMoreItems)
                return new LoadMoreItemsResult { Count = 0 };

            IsLoading = true;

            try
            {
                _currentPage++;
                var page = await _loadPageFunc(_currentPage, _pageSize, CancellationToken.None);

                if (page.Items.Count > 0)
                {
                    foreach (var item in page.Items)
                    {
                        Add(item);
                    }
                }

                TotalCount = page.TotalCount;
                _hasMoreItems = page.HasNext;

                return new LoadMoreItemsResult { Count = (uint)page.Items.Count };
            }
            catch
            {
                _currentPage--; // Rollback on error
                _hasMoreItems = false;
                return new LoadMoreItemsResult { Count = 0 };
            }
            finally
            {
                IsLoading = false;
            }
        }

        public void Reset()
        {
            Clear();
            _currentPage = 0;
            _hasMoreItems = true;
            _totalCount = 0;
        }

        protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        public new event PropertyChangedEventHandler? PropertyChanged;
    }

    /// <summary>
    /// Interface for incremental loading support
    /// </summary>
    public interface ISupportIncrementalLoading
    {
        bool HasMoreItems { get; }
        Task<LoadMoreItemsResult> LoadMoreItemsAsync(uint count);
    }

    /// <summary>
    /// Result of loading more items
    /// </summary>
    public struct LoadMoreItemsResult
    {
        public uint Count { get; set; }
    }

    /// <summary>
    /// Memory-efficient paged collection view for WPF DataGrid
    /// </summary>
    public class PagedCollectionView<T> : ICollectionView, INotifyPropertyChanged
    {
        private readonly List<T> _sourceList;
        private readonly int _pageSize;
        private List<T> _currentPageItems;
        private int _currentPage;
        private SortDescriptionCollection _sortDescriptions;
        private Predicate<object>? _filter;
        private object? _currentItem;
        private int _currentPosition;

        public event CurrentChangingEventHandler? CurrentChanging;
        public event EventHandler? CurrentChanged;
        public event PropertyChangedEventHandler? PropertyChanged;
        public event NotifyCollectionChangedEventHandler? CollectionChanged;

        public int PageSize => _pageSize;
        public int CurrentPage
        {
            get => _currentPage;
            set
            {
                if (value != _currentPage && value >= 1 && value <= TotalPages)
                {
                    _currentPage = value;
                    RefreshPage();
                    OnPropertyChanged(nameof(CurrentPage));
                }
            }
        }

        public int TotalPages => (int)Math.Ceiling(FilteredItemCount / (double)_pageSize);
        public int TotalItemCount => _sourceList.Count;
        public int FilteredItemCount => GetFilteredItems().Count();
        
        public bool CanMoveToFirstPage => CurrentPage > 1;
        public bool CanMoveToPreviousPage => CurrentPage > 1;
        public bool CanMoveToNextPage => CurrentPage < TotalPages;
        public bool CanMoveToLastPage => CurrentPage < TotalPages;

        public PagedCollectionView(IEnumerable<T> source, int pageSize = 50)
        {
            _sourceList = source?.ToList() ?? new List<T>();
            _pageSize = Math.Max(1, pageSize);
            _currentPage = 1;
            _currentPageItems = new List<T>();
            _sortDescriptions = new SortDescriptionCollection();
            RefreshPage();
        }

        public void MoveToFirstPage()
        {
            CurrentPage = 1;
        }

        public void MoveToPreviousPage()
        {
            if (CanMoveToPreviousPage)
                CurrentPage--;
        }

        public void MoveToNextPage()
        {
            if (CanMoveToNextPage)
                CurrentPage++;
        }

        public void MoveToLastPage()
        {
            CurrentPage = TotalPages;
        }

        private void RefreshPage()
        {
            var filtered = GetFilteredItems();
            var sorted = ApplySorting(filtered);
            
            _currentPageItems = sorted
                .Skip((_currentPage - 1) * _pageSize)
                .Take(_pageSize)
                .ToList();

            CollectionChanged?.Invoke(this, new NotifyCollectionChangedEventArgs(NotifyCollectionChangedAction.Reset));
            OnPropertyChanged(nameof(TotalPages));
            OnPropertyChanged(nameof(CanMoveToFirstPage));
            OnPropertyChanged(nameof(CanMoveToPreviousPage));
            OnPropertyChanged(nameof(CanMoveToNextPage));
            OnPropertyChanged(nameof(CanMoveToLastPage));
        }

        private IEnumerable<T> GetFilteredItems()
        {
            if (_filter == null)
                return _sourceList;

            return _sourceList.Where(item => _filter(item));
        }

        private IEnumerable<T> ApplySorting(IEnumerable<T> items)
        {
            if (_sortDescriptions.Count == 0)
                return items;

            IOrderedEnumerable<T>? orderedItems = null;

            foreach (var sortDesc in _sortDescriptions)
            {
                var property = typeof(T).GetProperty(sortDesc.PropertyName);
                if (property == null)
                    continue;

                if (orderedItems == null)
                {
                    orderedItems = sortDesc.Direction == ListSortDirection.Ascending
                        ? items.OrderBy(x => property.GetValue(x))
                        : items.OrderByDescending(x => property.GetValue(x));
                }
                else
                {
                    orderedItems = sortDesc.Direction == ListSortDirection.Ascending
                        ? orderedItems.ThenBy(x => property.GetValue(x))
                        : orderedItems.ThenByDescending(x => property.GetValue(x));
                }
            }

            return orderedItems ?? items;
        }

        // ICollectionView implementation
        public bool CanFilter => true;
        public bool CanGroup => false;
        public bool CanSort => true;
        public CultureInfo Culture { get; set; } = CultureInfo.CurrentCulture;
        public object? CurrentItem => _currentItem;
        public int CurrentPosition => _currentPosition;
        public bool IsCurrentAfterLast => _currentPosition >= _currentPageItems.Count;
        public bool IsCurrentBeforeFirst => _currentPosition < 0;
        public bool IsEmpty => _currentPageItems.Count == 0;
        public Predicate<object>? Filter
        {
            get => _filter;
            set
            {
                _filter = value;
                CurrentPage = 1;
                RefreshPage();
            }
        }
        public ObservableCollection<GroupDescription> GroupDescriptions => new();
        public ReadOnlyObservableCollection<object> Groups => new(new ObservableCollection<object>());
        public SortDescriptionCollection SortDescriptions => _sortDescriptions;
        public IEnumerable SourceCollection => _sourceList;

        public bool Contains(object item) => item is T t && _currentPageItems.Contains(t);
        public void Refresh() => RefreshPage();
        public IDisposable DeferRefresh() => new DeferHelper(this);
        public bool MoveCurrentTo(object item) => false; // Simplified
        public bool MoveCurrentToFirst() => false; // Simplified
        public bool MoveCurrentToLast() => false; // Simplified
        public bool MoveCurrentToNext() => false; // Simplified
        public bool MoveCurrentToPosition(int position) => false; // Simplified
        public bool MoveCurrentToPrevious() => false; // Simplified
        
        public IEnumerator GetEnumerator() => _currentPageItems.GetEnumerator();

        protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        private class DeferHelper : IDisposable
        {
            private readonly PagedCollectionView<T> _view;
            public DeferHelper(PagedCollectionView<T> view) => _view = view;
            public void Dispose() => _view.Refresh();
        }
    }

    /// <summary>
    /// Commands for pagination navigation
    /// </summary>
    public class PaginationCommands
    {
        public static readonly RoutedUICommand FirstPage = new(
            "First Page", "FirstPage", typeof(PaginationCommands),
            new InputGestureCollection { new KeyGesture(Key.Home, ModifierKeys.Control) });

        public static readonly RoutedUICommand PreviousPage = new(
            "Previous Page", "PreviousPage", typeof(PaginationCommands),
            new InputGestureCollection { new KeyGesture(Key.PageUp) });

        public static readonly RoutedUICommand NextPage = new(
            "Next Page", "NextPage", typeof(PaginationCommands),
            new InputGestureCollection { new KeyGesture(Key.PageDown) });

        public static readonly RoutedUICommand LastPage = new(
            "Last Page", "LastPage", typeof(PaginationCommands),
            new InputGestureCollection { new KeyGesture(Key.End, ModifierKeys.Control) });
    }
}