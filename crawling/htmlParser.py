import pandas as pd
from bs4 import BeautifulSoup
import os

def parseHtmlToCsv(htmlFile, csvFile):
    """
    Parses an HTML file from Card Gorilla to extract card information and saves it to a CSV file.

    Args:
        htmlFile (str): Path to the input HTML file.
        csvFile (str): Path to the output CSV file.
    """
    if not os.path.exists(htmlFile):
        print(f"Error: Input file not found at {htmlFile}")
        return

    with open(htmlFile, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    
    # Find all card containers
    cardContainers = soup.find_all("div", class_="card-container")
    
    if not cardContainers:
        print("No card data found in the HTML file.")
        return

    cardDataList = []
    for card in cardContainers:
        cardNameTag = card.find("span", class_="card_name")
        cardCorpTag = card.find("span", class_="card_corp")
        annualFeeTag = card.find("p", class_="in_for")
        performanceTag = card.find("p", class_="l_mth")
        cardImageTag = card.find("img") # Find the image tag
        cardImageUrl = cardImageTag["src"] if cardImageTag and "src" in cardImageTag.attrs else ""

        # Extract main benefits from the 'sale' div
        benefitsDiv = card.find("div", class_="sale")
        benefits = []
        if benefitsDiv:
            # Get text from all <p> tags inside the benefits div
            benefitItems = benefitsDiv.find_all("p")
            for item in benefitItems:
                benefits.append(item.get_text(strip=True, separator=" "))
        
        cardData = {
            "카드명": cardNameTag.get_text(strip=True) if cardNameTag else "",
            "카드사": cardCorpTag.get_text(strip=True) if cardCorpTag else "",
            "연회비": annualFeeTag.get_text(strip=True, separator=" / ") if annualFeeTag else "",
            "전월실적": performanceTag.get_text(strip=True, separator=" ") if performanceTag else "",
            "주요혜택": " | ".join(benefits),
            "카드이미지": cardImageUrl # Add card image URL
        }
        cardDataList.append(cardData)

    # Create a DataFrame and save to CSV
    df = pd.DataFrame(cardDataList)
    df.to_csv(csvFile, index=False, encoding="utf-8-sig")
    
    print(f"Successfully created {csvFile} with {len(cardDataList)} cards.")

if __name__ == "__main__":
    # Define file paths
    inputHtml = "card_gorilla_all.html"
    outputCsv = "card_gorilla_list.csv"
    
    # Run the parser
    parseHtmlToCsv(inputHtml, outputCsv)
