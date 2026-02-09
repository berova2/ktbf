#!/bin/bash
echo "denemeeeeee..."

if [ -f "deneme.txt" ]; then
    echo "Dosya zaten var."
else
    echo "Dosya oluşturuluyor..."
    touch deneme.txt
fi