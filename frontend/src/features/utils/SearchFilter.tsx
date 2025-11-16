import { useState } from 'react';
import { Card, CardContent } from '@/shared/ui/card';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { Checkbox } from '@/shared/ui/checkbox';
import { Button } from '@/shared/ui/button';
import { Search, Calendar, Filter, X } from 'lucide-react';

interface SearchFilterProps {
  onFilter: (searchTerm: string, dateFrom: string, dateTo: string, showCompleted: boolean) => void;
  totalCount: number;
}

export function SearchFilter({ onFilter, totalCount }: SearchFilterProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [showCompleted, setShowCompleted] = useState(true);
  const [showFilters, setShowFilters] = useState(false);

  const handleSearch = () => {
    onFilter(searchTerm, dateFrom, dateTo, showCompleted);
  };

  const handleReset = () => {
    setSearchTerm('');
    setDateFrom('');
    setDateTo('');
    setShowCompleted(true);
    onFilter('', '', '', true);
  };

  const hasActiveFilters = searchTerm || dateFrom || dateTo || !showCompleted;

  return (
    <Card>
      <CardContent className="pt-6 space-y-4">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="제목, 내용, 담당자로 검색..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                onFilter(e.target.value, dateFrom, dateTo, showCompleted);
              }}
              className="pl-10"
            />
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setShowFilters(!showFilters)}
            className={showFilters ? 'bg-blue-50' : ''}
          >
            <Filter className="w-4 h-4" />
          </Button>
          {hasActiveFilters && (
            <Button
              variant="outline"
              size="icon"
              onClick={handleReset}
              className="text-red-500 hover:text-red-700"
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
            <div className="space-y-2">
              <Label htmlFor="dateFrom" className="flex items-center gap-2 text-sm">
                <Calendar className="w-3 h-3" />
                시작 날짜
              </Label>
              <Input
                id="dateFrom"
                type="date"
                value={dateFrom}
                onChange={(e) => {
                  setDateFrom(e.target.value);
                  onFilter(searchTerm, e.target.value, dateTo, showCompleted);
                }}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="dateTo" className="flex items-center gap-2 text-sm">
                <Calendar className="w-3 h-3" />
                종료 날짜
              </Label>
              <Input
                id="dateTo"
                type="date"
                value={dateTo}
                onChange={(e) => {
                  setDateTo(e.target.value);
                  onFilter(searchTerm, dateFrom, e.target.value, showCompleted);
                }}
              />
            </div>

            <div className="flex items-end">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="showCompleted"
                  checked={showCompleted}
                  onCheckedChange={(checked) => {
                    const newValue = checked as boolean;
                    setShowCompleted(newValue);
                    onFilter(searchTerm, dateFrom, dateTo, newValue);
                  }}
                />
                <Label htmlFor="showCompleted" className="text-sm cursor-pointer">
                  완료된 회의록 표시
                </Label>
              </div>
            </div>
          </div>
        )}

        {hasActiveFilters && (
          <div className="pt-2 text-sm text-gray-600">
            총 {totalCount}개 중 검색 결과를 표시하고 있습니다
          </div>
        )}
      </CardContent>
    </Card>
  );
}
